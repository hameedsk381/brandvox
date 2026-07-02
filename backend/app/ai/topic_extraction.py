import json
import logging
from typing import List, Dict, Any
from app.ai.groq_client import get_groq_client
from app.ai.prompts import TOPICS_SYSTEM_PROMPT, TOPICS_USER_PROMPT

logger = logging.getLogger(__name__)

def _mock_topic_extraction(review_text: str) -> List[Dict[str, Any]]:
    text_lower = review_text.lower() if review_text else ""
    topics = []
    
    # Heuristics
    mappings = {
        "Food": ["food", "delicious", "burger", "taste", "eat", "menu", "sauce", "meal", "yummy", "fry", "salad", "pizza", "steak"],
        "Staff": ["staff", "waiter", "employee", "service", "waitress", "cashier", "manager", "server", "hostess", "people", "guy"],
        "Service": ["service", "helpful", "friendly", "rude", "polite", "attention", "care"],
        "Pricing": ["price", "expensive", "cost", "cheap", "overpriced", "worth", "value", "charged"],
        "Billing": ["bill", "receipt", "charge", "card", "pay", "payment"],
        "Hygiene": ["clean", "dirty", "dust", "bathroom", "washroom", "toilet", "hygiene", "messy"],
        "Wait Time": ["wait", "minutes", "hour", "delay", "slow", "line", "queue", "seated"],
        "Ambiance": ["music", "atmosphere", "vibe", "decor", "cozy", "noise", "loud", "beautiful"],
        "Parking": ["parking", "park", "garage", "lot", "valet"],
        "Product Quality": ["product", "quality", "item", "fabric", "material", "shoes", "clothes", "broken", "damaged"]
    }
    
    # Simple sentiment finder
    positive_indicators = ["great", "good", "excellent", "love", "friendly", "perfect", "delicious", "quick"]
    negative_indicators = ["bad", "rude", "slow", "dirty", "expensive", "worst", "poor", "overpriced", "disappointed", "cold"]
    
    def get_context_sentiment(word_list):
        # Scan words near found keywords
        for keyword in word_list:
            if keyword in text_lower:
                # Basic context check: find sentiment indicator in text
                pos_hits = sum(1 for w in positive_indicators if w in text_lower)
                neg_hits = sum(1 for w in negative_indicators if w in text_lower)
                if pos_hits > neg_hits:
                    return "positive"
                elif neg_hits > pos_hits:
                    return "negative"
                return "neutral"
        return None

    for topic_name, keywords in mappings.items():
        sentiment = get_context_sentiment(keywords)
        if sentiment:
            # Determine sub-topic if possible
            sub_topic = None
            if topic_name == "Food":
                for kw in ["burger", "pizza", "salad", "steak"]:
                    if kw in text_lower:
                        sub_topic = kw.capitalize()
                        break
            elif topic_name == "Wait Time":
                if "line" in text_lower or "queue" in text_lower:
                    sub_topic = "Queue"
                else:
                    sub_topic = "Service Speed"
            elif topic_name == "Staff":
                for kw in ["manager", "waiter", "server"]:
                    if kw in text_lower:
                        sub_topic = kw.capitalize()
                        break
                        
            topics.append({
                "topic": topic_name,
                "sub_topic": sub_topic,
                "sentiment": sentiment
            })
            
    # Always return at least one topic
    if not topics:
        topics.append({
            "topic": "Service",
            "sub_topic": "General",
            "sentiment": "neutral"
        })
        
    return topics

async def extract_topics(review_text: str) -> List[Dict[str, Any]]:
    if not review_text or not review_text.strip():
        return []

    groq = get_groq_client()
    
    # If API not configured, use mock
    if not groq.client:
        return _mock_topic_extraction(review_text)

    messages = [
        {"role": "system", "content": TOPICS_SYSTEM_PROMPT},
        {"role": "user", "content": TOPICS_USER_PROMPT.format(review_text=review_text)}
    ]
    
    response = await groq.chat_completion(messages, temperature=0.1, response_json=True)
    
    if response:
        try:
            cleaned = response.strip()
            if cleaned.startswith("```json"):
                cleaned = cleaned.split("```json")[1].split("```")[0].strip()
            elif cleaned.startswith("```"):
                cleaned = cleaned.split("```")[1].split("```")[0].strip()
                
            data = json.loads(cleaned)
            return data.get("topics", [])
        except Exception as e:
            logger.error(f"Failed to parse topics JSON response: {e}. Raw response: {response}")
            
    return _mock_topic_extraction(review_text)
