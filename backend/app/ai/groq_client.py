import json
import logging
import asyncio
from typing import Dict, Any, List, Optional
from groq import Groq
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

class GroqClient:
    def __init__(self):
        self.api_key = settings.GROQ_API_KEY
        if self.api_key and not self.api_key.startswith("your-"):
            self.client = Groq(api_key=self.api_key)
        else:
            logger.warning("Groq API key not set or placeholder. Mocking AI completions.")
            self.client = None

    async def chat_completion(
        self, 
        messages: List[Dict[str, str]], 
        temperature: float = 0.2, 
        max_tokens: int = 1000,
        response_json: bool = False
    ) -> Optional[str]:
        if not self.client:
            # Return empty or placeholder responses for mock mode
            return None
        
        # Groq client is synchronous. Run in a thread pool to avoid blocking the event loop.
        def _call_groq():
            extra_params = {}
            if response_json:
                extra_params["response_format"] = {"type": "json_object"}

            completion = self.client.chat.completions.create(
                messages=messages,
                model="openai/gpt-oss-120b",
                temperature=temperature,
                max_tokens=max_tokens,
                **extra_params
            )
            return completion.choices[0].message.content

        for attempt in range(3):
            try:
                loop = asyncio.get_event_loop()
                content = await loop.run_in_executor(None, _call_groq)
                return content
            except Exception as e:
                logger.error(f"Error calling Groq API (attempt {attempt + 1}): {e}")
                await asyncio.sleep(1 * (attempt + 1))
        
        return None

_groq_client = None

def get_groq_client() -> GroqClient:
    global _groq_client
    if _groq_client is None:
        _groq_client = GroqClient()
    return _groq_client
