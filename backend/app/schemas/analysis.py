from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel


class PriceLevelOut(BaseModel):
    price: Decimal
    level_type: str
    strength: float
    touch_count: int
    source: str
    first_seen_at: datetime
    last_tested_at: datetime
    role_flipped: bool


class PatternOut(BaseModel):
    name: str
    direction: str
    ts: datetime
    reliability_score: float
