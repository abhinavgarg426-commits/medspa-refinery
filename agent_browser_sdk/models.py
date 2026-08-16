"""
agent_browser_sdk/models.py
Pydantic models for type-safe API responses.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class PaymentReceipt(BaseModel):
    settled: bool = True
    cost_usd: float
    protocol: str = "x402"


class Venue(BaseModel):
    id: int
    name: str
    category: str
    sub_category: Optional[str] = None
    address: str
    city: Optional[str] = "Miami"
    neighborhood: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    price_level: Optional[str] = None
    overall_rating: float = 0.0
    safety_score: Optional[float] = None
    value_score: Optional[float] = None
    ambiance_score: Optional[float] = None
    service_score: Optional[float] = None
    verified_reviews_count: int = 0
    sentiment_tags: List[str] = Field(default_factory=list)
    phone: Optional[str] = None
    website: Optional[str] = None
    booking_url: Optional[str] = None
    wifi_speed_mbps: Optional[int] = None
    has_outdoor_seating: Optional[int] = None
    has_parking: Optional[int] = None
    is_accessible: Optional[int] = None
    agent_match_index: Optional[float] = None
    rationale: Optional[str] = Field(default=None, alias="_rationale")


class Offering(BaseModel):
    id: int
    venue_id: int
    category: str
    item: str
    description: Optional[str] = None
    price_usd: float
    unit: str
    tags: List[str] = Field(default_factory=list)


class SearchResult(BaseModel):
    status: str
    query: str
    classified_intent: Optional[str] = None
    matches_count: int
    data: List[Venue]
    payment_receipt: PaymentReceipt


class Recommendation(BaseModel):
    venue: Venue
    score: float
    rationale: str


class PricingAnalytics(BaseModel):
    item: str
    offering_category: str
    unit: str
    sample_size: int
    avg_price_usd: float
    min_price_usd: float
    max_price_usd: float
    price_spread_usd: float
    venues_offering_count: int