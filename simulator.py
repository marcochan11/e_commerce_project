import asyncio
import random
from datetime import datetime, timezone
from models import Product, Order
import logging

logger = logging.getLogger(__name__)

# Pre-defined data for seeding
CATEGORIES = ["Electronics", "Fashion", "Home & Garden", "Sports", "Books"]
REGIONS = ["North America", "Europe", "Asia-Pacific", "Latin America"]
PRODUCT_NAMES = {
    "Electronics": ["Wireless Earbuds", "Smart Watch", "4K Monitor", "Mechanical Keyboard", "Gaming Mouse", "USB-C Hub"],
    "Fashion": ["Denim Jacket", "Running Shoes", "Cotton T-Shirt", "Leather Belt", "Sunglasses", "Backpack"],
    "Home & Garden": ["LED Desk Lamp", "Plant Pot", "Throw Pillow", "Coffee Maker", "Air Purifier", "Wall Clock"],
    "Sports": ["Yoga Mat", "Dumbbell Set", "Water Bottle", "Resistance Bands", "Cycling Helmet", "Foam Roller"],
    "Books": ["Data Engineering 101", "Python Cookbook", "Sci-Fi Novel", "History of Art", "Business Strategy", "Cooking Guide"]
}

class ECommerceSimulator:
    def __init__(self, db):
        self.db = db
        self.is_running = False
        self.task = None

    async def seed_products(self):
        """Seed database with initial products if empty"""
        count = await self.db.products.count_documents({})
        if count > 0:
            return

        products = []
        for category in CATEGORIES:
            names = PRODUCT_NAMES[category]
            for name in names:
                products.append(Product(
                    name=name,
                    category=category,
                    price=round(random.uniform(20.0, 500.0), 2),
                    stock=random.randint(50, 200),
                    low_stock_threshold=15
                ).model_dump())
        
        # Fix datetime for mongo
        for p in products:
            p['last_updated'] = p['last_updated'].isoformat()

        if products:
            await self.db.products.insert_many(products)
            logger.info(f"Seeded {len(products)} products.")

    async def generate_order(self):
        """Create a random order from existing products"""
        # Get a random product with stock > 0
        pipeline = [{"$match": {"stock": {"$gt": 0}}}, {"$sample": {"size": 1}}]
        products = await self.db.products.aggregate(pipeline).to_list(1)
        
        if not products:
            logger.warning("No products with stock available!")
            return

        prod_data = products[0]
        # Create Order
        qty = random.choices([1, 2, 3, 4, 5], weights=[60, 20, 10, 5, 5])[0]
        # Check if we have enough stock
        if prod_data['stock'] < qty:
            qty = prod_data['stock']
            
        total_price = round(prod_data['price'] * qty, 2)
        
        order = Order(
            product_id=prod_data['id'],
            product_name=prod_data['name'],
            category=prod_data['category'],
            quantity=qty,
            total_price=total_price,
            region=random.choice(REGIONS)
        )
        
        # DB Operations
        # 1. Insert Order
        order_doc = order.model_dump()
        order_doc['timestamp'] = order_doc['timestamp'].isoformat()
        await self.db.orders.insert_one(order_doc)
        
        # 2. Update Stock
        await self.db.products.update_one(
            {"id": prod_data['id']},
            {"$inc": {"stock": -qty}}
        )
        
        logger.info(f"Generated Order: {order.product_name} x{qty} - ${total_price}")

        # Occasional Restock Event (to keep simulation going indefinitely)
        if random.random() < 0.1: # 10% chance
            await self.restock_random_product()

    async def restock_random_product(self):
        """Randomly restock a low stock item"""
        low_stock = await self.db.products.find({"stock": {"$lt": 20}}).to_list(5)
        if low_stock:
            target = random.choice(low_stock)
            restock_amount = random.randint(20, 50)
            await self.db.products.update_one(
                {"id": target['id']},
                {"$inc": {"stock": restock_amount}}
            )
            logger.info(f"Restocked {target['name']} (+{restock_amount})")

    async def run_loop(self):
        logger.info("Simulation Loop Started")
        while self.is_running:
            try:
                await self.generate_order()
                # Random delay between orders (0.5s to 3s) for realistic feel
                await asyncio.sleep(random.uniform(0.5, 3.0))
            except Exception as e:
                logger.error(f"Error in simulation loop: {e}")
                await asyncio.sleep(1)

    def start(self):
        if not self.is_running:
            self.is_running = True
            self.task = asyncio.create_task(self.run_loop())
            return True
        return False

    def stop(self):
        self.is_running = False
        if self.task:
            self.task.cancel()
        return True