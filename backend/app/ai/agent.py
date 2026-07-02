import json
import logging
import asyncio
import uuid
from typing import AsyncGenerator, Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.ai.groq_client import get_groq_client
from app.models.chat import ChatSession, ChatMessage, MessageRole, SessionType
from app.models.analytics import ReputationScore
from app.models.review import Review

logger = logging.getLogger(__name__)

MANAGER_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_reputation_score",
            "description": "Get the most recent reputation score and stats for a location",
            "parameters": {
                "type": "object",
                "properties": {
                    "location_id": {"type": "string", "description": "The UUID of the location"}
                },
                "required": ["location_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_recent_reviews",
            "description": "Get the most recent reviews for a location",
            "parameters": {
                "type": "object",
                "properties": {
                    "location_id": {"type": "string", "description": "The UUID of the location"},
                    "limit": {"type": "integer", "description": "Number of reviews to return, max 10"}
                },
                "required": ["location_id", "limit"],
            },
        },
    }
]

CUSTOMER_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "log_complaint",
            "description": "Log a customer complaint securely so the business can follow up. Use this instead of encouraging a public review if they are angry.",
            "parameters": {
                "type": "object",
                "properties": {
                    "complaint_summary": {"type": "string", "description": "Summary of the complaint"}
                },
                "required": ["complaint_summary"],
            },
        },
    }
]

async def execute_tool(name: str, args: Dict[str, Any], db: AsyncSession) -> str:
    if name == "get_reputation_score":
        location_id_str = args.get("location_id")
        try:
            loc_uuid = uuid.UUID(location_id_str)
        except (ValueError, TypeError):
            return json.dumps({"error": "Invalid location_id format."})
            
        stmt = select(ReputationScore).where(ReputationScore.location_id == loc_uuid).order_by(ReputationScore.score_date.desc()).limit(1)
        result = await db.execute(stmt)
        score = result.scalar_one_or_none()
        if score:
            return json.dumps({
                "overall_score": score.overall_score,
                "avg_rating": score.avg_rating,
                "total_reviews": score.review_volume,
                "sentiment_score": score.sentiment_score
            })
        return json.dumps({"error": "No reputation score found for this location."})
        
    elif name == "get_recent_reviews":
        location_id_str = args.get("location_id")
        try:
            loc_uuid = uuid.UUID(location_id_str)
        except (ValueError, TypeError):
            return json.dumps({"error": "Invalid location_id format."})
            
        limit = min(args.get("limit", 5), 10)
        stmt = select(Review).where(Review.location_id == loc_uuid).order_by(Review.review_date.desc()).limit(limit)
        result = await db.execute(stmt)
        reviews = result.scalars().all()
        return json.dumps([
            {"rating": r.rating, "text": r.text, "source": r.source, "date": str(r.review_date)}
            for r in reviews
        ])
        
    elif name == "log_complaint":
        summary = args.get("complaint_summary")
        # In a real app, we would save this to a SupportTicket or Complaint table
        logger.info(f"Logged customer complaint: {summary}")
        return json.dumps({"status": "success", "message": "Complaint has been logged and sent to the team."})
        
    return json.dumps({"error": f"Unknown tool {name}"})

async def run_chat_agent(session: ChatSession, db: AsyncSession, new_user_message: str, location_id: str = None, location_name: str = None) -> AsyncGenerator[str, None]:
    # 1. Save user message
    user_msg = ChatMessage(
        session_id=str(session.id),
        role=MessageRole.user,
        content=new_user_message
    )
    db.add(user_msg)
    await db.commit()
    
    # 2. Build conversation history
    stmt = select(ChatMessage).where(ChatMessage.session_id == str(session.id)).order_by(ChatMessage.created_at.asc())
    result = await db.execute(stmt)
    history = result.scalars().all()
    
    messages = []
    
    # Add system prompt based on session type
    if session.session_type == SessionType.manager:
        sys_prompt = "You are the ReputationOS AI Copilot. You assist brand managers in analyzing their reputation, reviews, and customer sentiment. You can query the database using tools."
        if location_id and location_name:
            sys_prompt += f" IMPORTANT CONTEXT: The user is currently viewing the dashboard for location '{location_name}' (ID: {location_id}). Automatically use this location_id for any tools unless they specify a different one. DO NOT ASK the user for a location ID."
        else:
            sys_prompt += " If you don't know the location_id, ask the user."
            
        logger.info(f"Generated sys_prompt: {sys_prompt}")
        messages.append({"role": "system", "content": sys_prompt})
        tools = MANAGER_TOOLS
    else:
        messages.append({"role": "system", "content": "You are a helpful customer support chatbot. You represent the brand. If a customer is angry, apologize and use the log_complaint tool to capture their feedback internally."})
        tools = CUSTOMER_TOOLS
        
    for msg in history:
        if msg.role == MessageRole.user:
            messages.append({"role": "user", "content": msg.content})
        elif msg.role == MessageRole.assistant:
            if msg.tool_calls:
                messages.append({"role": "assistant", "tool_calls": msg.tool_calls})
            else:
                messages.append({"role": "assistant", "content": msg.content})
        elif msg.role == MessageRole.tool:
            messages.append({"role": "tool", "content": msg.content, "tool_call_id": msg.tool_call_id})

    # 3. Agent Loop
    client = get_groq_client()
    if not client.client:
        yield json.dumps({"type": "message", "content": "AI is in mock mode."})
        return
        
    for _ in range(5): # Max 5 turns per request
        def _call():
            return client.client.chat.completions.create(
                model="openai/gpt-oss-120b",
                messages=messages,
                tools=tools,
                tool_choice="auto",
                temperature=0.2
            )
        
        loop = asyncio.get_event_loop()
        completion = await loop.run_in_executor(None, _call)
        message = completion.choices[0].message
        
        if message.tool_calls:
            # Add assistant message with tool calls to history
            tool_calls_dict = [
                {"id": tc.id, "type": tc.type, "function": {"name": tc.function.name, "arguments": tc.function.arguments}}
                for tc in message.tool_calls
            ]
            messages.append({"role": "assistant", "tool_calls": tool_calls_dict})
            
            # Save assistant tool call message to DB
            ast_msg = ChatMessage(
                session_id=str(session.id),
                role=MessageRole.assistant,
                tool_calls=tool_calls_dict
            )
            db.add(ast_msg)
            await db.commit()
            
            # Execute tools
            for tool_call in message.tool_calls:
                fn_name = tool_call.function.name
                fn_args = json.loads(tool_call.function.arguments)
                
                yield json.dumps({"type": "tool_call", "name": fn_name})
                
                result_str = await execute_tool(fn_name, fn_args, db)
                
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": result_str
                })
                
                # Save tool result to DB
                tool_msg = ChatMessage(
                    session_id=str(session.id),
                    role=MessageRole.tool,
                    tool_call_id=tool_call.id,
                    content=result_str
                )
                db.add(tool_msg)
            await db.commit()
            # Loop continues to send tool results back to LLM
            
        else:
            # Final response
            final_content = message.content
            ast_msg = ChatMessage(
                session_id=str(session.id),
                role=MessageRole.assistant,
                content=final_content
            )
            db.add(ast_msg)
            await db.commit()
            
            yield json.dumps({"type": "message", "content": final_content})
            break
