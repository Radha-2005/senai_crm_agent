"""
schemas/analytics.py - Pydantic schemas for analytics and dashboard data.
"""
from pydantic import BaseModel
from typing import Dict, List, Optional
from datetime import datetime


class ClassificationStats(BaseModel):
    label: str
    count: int
    percentage: float


class SentimentStats(BaseModel):
    label: str
    count: int


class DashboardStats(BaseModel):
    total_emails: int
    processed_today: int
    pending: int
    escalated: int
    legal_flagged: int
    auto_replied: int
    avg_processing_time_sec: Optional[float]
    classification_breakdown: List[ClassificationStats]
    sentiment_breakdown: List[SentimentStats]
    decision_breakdown: Dict[str, int]


class VolumePoint(BaseModel):
    date: str
    count: int


class AnalyticsTrend(BaseModel):
    volume: List[VolumePoint]
    escalation_rate: float
    avg_sentiment_score: float
