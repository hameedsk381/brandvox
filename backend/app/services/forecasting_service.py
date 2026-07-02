import json
import logging
from uuid import UUID
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import desc

from app.models.review import Review
from app.models.forecast import Forecast
from app.ai.groq_client import get_groq_client

logger = logging.getLogger(__name__)

async def get_historical_dataset(db: AsyncSession, location_id: UUID) -> List[Dict[str, Any]]:
    # Fetch all reviews for the location over the past 6 months
    six_months_ago = datetime.utcnow() - timedelta(days=180)
    result = await db.execute(
        select(Review)
        .filter(Review.location_id == location_id)
        .filter(Review.review_date >= six_months_ago)
        .order_by(Review.review_date)
    )
    reviews = result.scalars().all()
    
    # Group by Month-Year string (e.g., "2026-01")
    months_data = {}
    
    for r in reviews:
        if not r.review_date:
            continue
        m_key = r.review_date.strftime("%b %Y")
        if m_key not in months_data:
            months_data[m_key] = {"ratings": [], "count": 0}
        months_data[m_key]["ratings"].append(r.rating)
        months_data[m_key]["count"] += 1
        
    dataset = []
    for m_key, data in months_data.items():
        avg_rating = sum(data["ratings"]) / len(data["ratings"]) if data["ratings"] else 0
        dataset.append({
            "month": m_key,
            "average_rating": round(avg_rating, 2),
            "review_volume": data["count"]
        })
        
    # Ensure dataset is chronological (it should be since reviews were ordered, but dict insertion order handles it in 3.7+)
    return dataset

async def generate_forecast(db: AsyncSession, location_id: UUID) -> Forecast:
    dataset = await get_historical_dataset(db, location_id)
    
    if not dataset:
        # Generate dummy dataset if no reviews exist
        dataset = [
            {"month": (datetime.utcnow() - timedelta(days=60)).strftime("%b %Y"), "average_rating": 4.5, "review_volume": 10},
            {"month": (datetime.utcnow() - timedelta(days=30)).strftime("%b %Y"), "average_rating": 4.3, "review_volume": 15},
            {"month": datetime.utcnow().strftime("%b %Y"), "average_rating": 4.1, "review_volume": 22}
        ]
        
    groq = get_groq_client()
    system_prompt = (
        "You are an AI Forecasting Agent for ReputationOS. Given the following historical review data (grouped by month), "
        "predict the metrics for the next upcoming month. "
        "Analyze trends in ratings and volume to estimate customer churn risk, reputation risks, and seasonal shifts.\n\n"
        "Return ONLY a JSON object matching this schema:\n"
        "{\n"
        "  \"predicted_rating\": float (1.0 - 5.0),\n"
        "  \"predicted_volume\": int,\n"
        "  \"churn_risk_score\": int (0 - 100, higher means higher risk of customers leaving),\n"
        "  \"reputation_risks\": [string, string, ...],\n"
        "  \"seasonal_trends\": [string, string, ...],\n"
        "  \"actionable_advice\": string\n"
        "}"
    )
    
    forecast_data = {
        "predicted_rating": 4.0,
        "predicted_volume": 20,
        "churn_risk_score": 30,
        "reputation_risks": ["Minor drop in service quality"],
        "seasonal_trends": ["Volume stabilizing"],
        "actionable_advice": "Maintain current service levels."
    }
    
    if groq.client:
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Historical Dataset: {json.dumps(dataset)}"}
        ]
        completion = await groq.chat_completion(messages, temperature=0.3, response_json=True)
        if completion:
            try:
                cleaned = completion.strip()
                if cleaned.startswith("```json"):
                    cleaned = cleaned.split("```json")[1].split("```")[0].strip()
                elif cleaned.startswith("```"):
                    cleaned = cleaned.split("```")[1].split("```")[0].strip()
                parsed = json.loads(cleaned)
                forecast_data.update(parsed)
            except Exception as e:
                logger.error(f"Failed to parse AI forecast JSON: {e}")
                
    forecast = Forecast(
        location_id=location_id,
        predicted_rating=forecast_data.get("predicted_rating", 4.0),
        predicted_volume=forecast_data.get("predicted_volume", 20),
        churn_risk_score=forecast_data.get("churn_risk_score", 30),
        reputation_risks=forecast_data.get("reputation_risks", []),
        seasonal_trends=forecast_data.get("seasonal_trends", []),
        actionable_advice=forecast_data.get("actionable_advice", "")
    )
    
    db.add(forecast)
    await db.commit()
    await db.refresh(forecast)
    
    return forecast

async def get_latest_forecast(db: AsyncSession, location_id: UUID) -> Forecast:
    # Check if a forecast was generated in the last 24 hours
    one_day_ago = datetime.utcnow() - timedelta(days=1)
    
    result = await db.execute(
        select(Forecast)
        .filter(Forecast.location_id == location_id)
        .filter(Forecast.forecast_date >= one_day_ago)
        .order_by(desc(Forecast.forecast_date))
    )
    
    forecast = result.scalars().first()
    if forecast:
        return forecast
        
    # Generate a new one
    return await generate_forecast(db, location_id)
