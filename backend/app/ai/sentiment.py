import json
import logging
from typing import Dict, Any
from app.ai.groq_client import get_groq_client
from app.ai.prompts import SENTIMENT_SYSTEM_PROMPT, SENTIMENT_USER_PROMPT

logger = logging.getLogger(__name__)

def analyze_sentiment_keyword(review_text: str) -> Dict[str, Any]:
    text_lower = review_text.lower() if review_text else ""
    
    # Simple keyword heuristic
    positive_words = ["great", "excellent", "love", "perfect", "good", "friendly", "delicious", "amazing", "best", "happy"]
    negative_words = ["bad", "worst", "slow", "rude", "dirty", "poor", "disappointed", "cold", "expensive", "wait", "parking", "overpriced", "terrible", "awful"]
    
    pos_count = sum(1 for w in positive_words if w in text_lower)
    neg_count = sum(1 for w in negative_words if w in text_lower)
    
    if pos_count > neg_count:
        sentiment = "positive"
        confidence = 0.8 + (0.02 * min(pos_count, 10))
        emotions = ["satisfied", "happy"]
        if "love" in text_lower or "best" in text_lower:
            emotions.append("loyal")
    elif neg_count > pos_count:
        sentiment = "negative"
        confidence = 0.8 + (0.02 * min(neg_count, 10))
        emotions = ["disappointed"]
        if "rude" in text_lower or "slow" in text_lower:
            emotions.append("frustrated")
        if "worst" in text_lower or "angry" in text_lower:
            emotions.append("angry")
    elif pos_count == 0 and neg_count == 0:
        sentiment = "neutral"
        confidence = 0.9
        emotions = ["neutral"]
    else:
        sentiment = "mixed"
        confidence = 0.7
        emotions = ["confused", "satisfied", "disappointed"]
        
    return {
        "sentiment": sentiment,
        "confidence": round(confidence, 2),
        "emotions": emotions
    }

async def analyze_sentiment(review_text: str) -> Dict[str, Any]:
    if not review_text or not review_text.strip():
        return {
            "sentiment": "neutral",
            "confidence": 1.0,
            "emotions": ["neutral"]
        }

    groq = get_groq_client()
    
    # If groq API is not set, use local mock
    if not groq.client:
        return analyze_sentiment_keyword(review_text)

    messages = [
        {"role": "system", "content": SENTIMENT_SYSTEM_PROMPT},
        {"role": "user", "content": SENTIMENT_USER_PROMPT.format(review_text=review_text)}
    ]
    
    response = await groq.chat_completion(messages, temperature=0.1, response_json=True)
    
    if response:
        try:
            # Strip markdown block formatting if LLM generated it despite system instructions
            cleaned = response.strip()
            if cleaned.startswith("```json"):
                cleaned = cleaned.split("```json")[1].split("```")[0].strip()
            elif cleaned.startswith("```"):
                cleaned = cleaned.split("```")[1].split("```")[0].strip()
                
            data = json.loads(cleaned)
            return {
                "sentiment": data.get("sentiment", "neutral"),
                "confidence": data.get("confidence", 0.8),
                "emotions": data.get("emotions", ["neutral"])
            }
        except Exception as e:
            logger.error(f"Failed to parse sentiment JSON response: {e}. Raw response: {response}")
            
    # Fallback to mock on failure
    return analyze_sentiment_keyword(review_text)
