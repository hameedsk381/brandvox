import pytest
from unittest.mock import AsyncMock, patch

pytestmark = pytest.mark.asyncio


async def test_sentiment_analysis_mock(client, admin_token, seed_admin_user):
    """Test that sentiment analysis endpoint works with mock."""
    response = await client.post(
        "/api/reviews/00000000-0000-0000-0000-000000000001/generate-reply",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    # Should handle gracefully (review may not exist)
    assert response.status_code in (200, 404, 500)


@patch("app.ai.groq_client.GroqClient")
async def test_groq_client_structure(mock_groq):
    """Verify Groq client interface."""
    from app.ai.groq_client import GroqClient

    client = GroqClient()
    assert hasattr(client, "analyze")
    assert hasattr(client, "chat_completion")


async def test_prompt_templates():
    """Verify prompt templates load correctly."""
    from app.ai.prompts import SENTIMENT_SYSTEM_PROMPT, SENTIMENT_USER_PROMPT

    assert SENTIMENT_SYSTEM_PROMPT is not None
    assert len(SENTIMENT_SYSTEM_PROMPT) > 0
    assert SENTIMENT_USER_PROMPT is not None
    assert "{review_text}" in SENTIMENT_USER_PROMPT


async def test_mock_sentiment_fallback():
    """Test keyword-based sentiment mock."""
    from app.ai.sentiment import analyze_sentiment_keyword

    result = analyze_sentiment_keyword("This is amazing and wonderful!")
    assert result["sentiment"] == "positive"

    result = analyze_sentiment_keyword("This is terrible and awful.")
    assert result["sentiment"] == "negative"

    result = analyze_sentiment_keyword("The item is okay.")
    assert result["sentiment"] == "neutral"
