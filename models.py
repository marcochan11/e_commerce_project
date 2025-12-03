from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
from datetime import datetime, timezone
import uuid

class Product(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    category: str
    price: float
    stock: int
    low_stock_threshold: int = 10
    last_updated: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class Order(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    product_id: str
    product_name: str
    category: str
    quantity: int
    total_price: float
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    region: str = "Global"  # NA, EU, ASIA, etc.

class DashboardStats(BaseModel):
    total_revenue: float
    total_orders: int
    low_stock_count: int
    top_category: str