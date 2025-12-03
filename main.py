from fastapi import FastAPI, APIRouter, HTTPException
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from typing import List
from datetime import datetime, timezone

# Import our new modules
from models import Product, Order, DashboardStats
from simulator import ECommerceSimulator

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# DB Setup
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Initialize Simulator
simulator = ECommerceSimulator(db)

app = FastAPI()
api_router = APIRouter(prefix="/api")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Endpoints ---

@app.on_event("startup")
async def startup_event():
    # Seed data on startup
    await simulator.seed_products()
    # Auto-start simulation for instant gratification
    simulator.start()

@api_router.get("/simulation/status")
async def get_sim_status():
    return {"running": simulator.is_running}

@api_router.post("/simulation/toggle")
async def toggle_simulation(running: bool):
    if running:
        simulator.start()
    else:
        simulator.stop()
    return {"running": simulator.is_running}

@api_router.get("/dashboard/stats", response_model=DashboardStats)
async def get_dashboard_stats():
    # Today's Stats
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    today_iso = today_start.isoformat()

    pipeline = [
        {"$match": {"timestamp": {"$gte": today_iso}}},
        {"$group": {
            "_id": None,
            "total_revenue": {"$sum": "$total_price"},
            "total_orders": {"$count": {}}
        }}
    ]
    
    stats_res = await db.orders.aggregate(pipeline).to_list(1)
    
    total_rev = 0.0
    total_orders = 0
    if stats_res:
        total_rev = round(stats_res[0]['total_revenue'], 2)
        total_orders = stats_res[0]['total_orders']

    # Low Stock Count
    low_stock_count = await db.products.count_documents({"stock": {"$lt": 15}})

    # Top Category
    cat_pipeline = [
        {"$group": {"_id": "$category", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 1}
    ]
    top_cat_res = await db.orders.aggregate(cat_pipeline).to_list(1)
    top_cat = top_cat_res[0]['_id'] if top_cat_res else "N/A"

    return DashboardStats(
        total_revenue=total_rev,
        total_orders=total_orders,
        low_stock_count=low_stock_count,
        top_category=top_cat
    )

@api_router.get("/dashboard/recent-orders", response_model=List[Order])
async def get_recent_orders():
    orders_data = await db.orders.find({}, {"_id": 0}).sort("timestamp", -1).limit(20).to_list(20)
    # Convert ISO strings back to datetime
    for o in orders_data:
        if isinstance(o['timestamp'], str):
            o['timestamp'] = datetime.fromisoformat(o['timestamp'])
    return orders_data

@api_router.get("/dashboard/sales-chart")
async def get_sales_chart_data():
    """Get last 50 orders for the chart"""
    orders = await db.orders.find({}, {"_id": 0, "timestamp": 1, "total_price": 1}).sort("timestamp", -1).limit(50).to_list(50)
    orders.reverse()
    return orders

@api_router.get("/dashboard/category-dist")
async def get_category_distribution():
    pipeline = [
        {"$group": {"_id": "$category", "value": {"$sum": 1}}}
    ]
    data = await db.orders.aggregate(pipeline).to_list(None)
    return [{"name": d["_id"], "value": d["value"]} for d in data]

@api_router.get("/inventory", response_model=List[Product])
async def get_inventory():
    products = await db.products.find({}, {"_id": 0}).to_list(1000)
    for p in products:
        if isinstance(p['last_updated'], str):
            p['last_updated'] = datetime.fromisoformat(p['last_updated'])
    return products

@api_router.post("/inventory/restock/{product_id}")
async def restock_product(product_id: str):
    result = await db.products.update_one(
        {"id": product_id},
        {"$inc": {"stock": 50}}
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Product not found")
    return {"message": "Restocked successfully"}

app.include_router(api_router)

@app.on_event("shutdown")
async def shutdown_event():
    simulator.stop()
    client.close()