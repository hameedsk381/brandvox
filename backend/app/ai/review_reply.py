import json
import logging
from typing import List, Dict, Any, Optional
from app.ai.groq_client import get_groq_client
from app.ai.prompts import REPLY_SYSTEM_PROMPT, REPLY_USER_PROMPT

logger = logging.getLogger(__name__)

def _mock_reply_generation(
    review_text: str,
    rating: int,
    brand_voice: Dict[str, Any],
    business_name: str,
    author_name: Optional[str] = None
) -> List[Dict[str, Any]]:
    # Extract voice preferences
    tone = brand_voice.get("tone", "professional")
    greeting_style = brand_voice.get("greeting_style", "Dear [Name],")
    closing_style = brand_voice.get("closing_style", "Best regards, The Team")
    
    author = author_name if author_name else "Valued Customer"
    
    # Format greeting/closing
    greeting = greeting_style.replace("[Name]", author).replace("[Author]", author)
    closing = closing_style.replace("[Business]", business_name).replace("[BusinessName]", business_name)
    
    # Mock template combinations based on rating and tone
    if rating >= 4:
        if tone == "casual":
            opt1 = f"{greeting}\n\nAwesome! Thanks for sharing this. We're super pumped that you enjoyed your experience with us. Can't wait to have you back again soon!\n\n{closing}"
            opt2 = f"{greeting}\n\nWow, thanks for the review! The team is stoked to hear you had a great time. Let us know next time you drop by so we can say hi!\n\n{closing}"
        elif tone == "medical":
            opt1 = f"{greeting}\n\nThank you for sharing your positive feedback. We are pleased to hear you had an excellent experience. Our medical team is dedicated to providing high-quality care, and your review motivates us to keep doing our best. Wishing you good health.\n\n{closing}"
            opt2 = f"{greeting}\n\nWe appreciate you taking the time to share your experience. Your health and comfort are our top priorities, and we are glad we met your expectations. Please reach out if you need anything in the future.\n\n{closing}"
        elif tone == "premium":
            opt1 = f"{greeting}\n\nThank you for your gracious review. We are delighted that your experience was nothing short of exceptional. We take great pride in our high standards of quality and service, and we look forward to welcoming you back for another exquisite visit.\n\n{closing}"
            opt2 = f"{greeting}\n\nWe are deeply honored by your complimentary feedback. It is our absolute pleasure to ensure each detail of your experience is tailored to perfection. We await your return.\n\n{closing}"
        else: # professional, corporate, hospitality, etc.
            opt1 = f"{greeting}\n\nThank you very much for your feedback. We are glad to hear that you had a positive experience at {business_name}. Your satisfaction is our primary goal, and we look forward to serving you again in the future.\n\n{closing}"
            opt2 = f"{greeting}\n\nWe appreciate you taking the time to write this review. It is wonderful to hear that our team met your expectations. We look forward to your next visit.\n\n{closing}"
    elif rating == 3:
        if tone == "casual":
            opt1 = f"{greeting}\n\nThanks for the feedback. Glad things were okay, but we'd love to make your next visit a 5-star one! Let us know if you have any tips on what we can improve.\n\n{closing}"
            opt2 = f"{greeting}\n\nThanks for review. We hear you! We're always working to get better, so we'll share your notes with the crew to make sure we level up next time.\n\n{closing}"
        else:
            opt1 = f"{greeting}\n\nThank you for your review. We are glad you found our services satisfactory, but we noticed there is room for improvement. We value your feedback and will use it to enhance our services.\n\n{closing}"
            opt2 = f"{greeting}\n\nThank you for sharing your experience. We appreciate your honest rating and will address the aspects of your visit that fell short of a five-star standard. We hope to have the opportunity to serve you better next time.\n\n{closing}"
    else: # 1 or 2 stars
        if tone == "casual":
            opt1 = f"{greeting}\n\nOh no, we're really sorry to hear that things didn't go well. We want to make this right. Please shoot us an email or drop us a line so we can check out what happened and fix it for you.\n\n{closing}"
            opt2 = f"{greeting}\n\nSo sorry for the letdown! That's definitely not how we roll. We'd love the chance to make it up to you if you're open to letting us know how to contact you.\n\n{closing}"
        elif tone == "medical":
            opt1 = f"{greeting}\n\nWe are deeply concerned to read about your negative experience. The care and safety of our patients is our utmost priority. We would appreciate the opportunity to discuss your experience privately to resolve this. Please contact our patient relations department.\n\n{closing}"
            opt2 = f"{greeting}\n\nThank you for bringing this to our attention. We hold ourselves to strict patient care standards, and we sincerely apologize that we fell short in your case. Please contact our office manager directly so we can address your concerns immediately.\n\n{closing}"
        else:
            opt1 = f"{greeting}\n\nThank you for your review. We sincerely apologize that your experience did not meet your expectations. We take all feedback very seriously and would appreciate the opportunity to investigate your concerns further. Please contact us directly so we can assist you.\n\n{closing}"
            opt2 = f"{greeting}\n\nWe are very sorry to hear about your dissatisfactory experience at {business_name}. This does not reflect our standards of service. We would appreciate the chance to connect with you and make things right. Please reach out to us at your earliest convenience.\n\n{closing}"
            
    return [
        {"option_index": 1, "content": opt1},
        {"option_index": 2, "content": opt2}
    ]

async def generate_reply(
    review_text: str,
    rating: int,
    brand_voice: Dict[str, Any],
    business_name: str,
    industry: str,
    author_name: Optional[str] = None
) -> List[Dict[str, Any]]:
    groq = get_groq_client()
    
    # If API not configured, use mock
    if not groq.client:
        return _mock_reply_generation(review_text, rating, brand_voice, business_name, author_name)

    messages = [
        {"role": "system", "content": REPLY_SYSTEM_PROMPT},
        {"role": "user", "content": REPLY_USER_PROMPT.format(
            review_text=review_text,
            rating=rating,
            business_name=business_name,
            industry=industry or "General Business",
            tone=brand_voice.get("tone", "professional"),
            traits=", ".join(brand_voice.get("personality_traits", ["professional", "helpful"])),
            greeting_style=brand_voice.get("greeting_style", "Dear [Name],"),
            closing_style=brand_voice.get("closing_style", "Best regards, The Team"),
            vocabulary_notes=brand_voice.get("vocabulary_notes", "No specific vocabulary constraints")
        )}
    ]
    
    response = await groq.chat_completion(messages, temperature=0.7, response_json=True)
    
    if response:
        try:
            cleaned = response.strip()
            if cleaned.startswith("```json"):
                cleaned = cleaned.split("```json")[1].split("```")[0].strip()
            elif cleaned.startswith("```"):
                cleaned = cleaned.split("```")[1].split("```")[0].strip()
                
            data = json.loads(cleaned)
            replies = data.get("replies", [])
            # Format custom name references
            author = author_name if author_name else "Valued Customer"
            for reply in replies:
                content = reply.get("content", "")
                content = content.replace("[Name]", author).replace("[Author]", author)
                content = content.replace("[Business]", business_name).replace("[BusinessName]", business_name)
                reply["content"] = content
            return replies
        except Exception as e:
            logger.error(f"Failed to parse reply JSON response: {e}. Raw response: {response}")
            
    return _mock_reply_generation(review_text, rating, brand_voice, business_name, author_name)
