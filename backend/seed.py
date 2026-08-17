"""Seed database with realistic demo data."""

from __future__ import annotations

import random
import uuid
from datetime import datetime, timedelta, timezone

from app.core.security import get_password_hash
from app.db.init_db import init_db
from app.db.session import SessionLocal
from app.models.forecast import Alert, ReorderRecommendation
from app.models.inventory import Inventory, InventoryTransaction
from app.models.product import Category, Product, Supplier
from app.models.sales import Sale, SalesItem
from app.models.user import Role, User
from app.services.alert_service import generate_alerts
from app.services.intelligence_service import generate_all_recommendations

CATEGORIES = [
    ("Electronics", "Computers, peripherals, and accessories"),
    ("Office Supplies", "Desk accessories and stationery"),
    ("Networking", "Routers, cables, and network equipment"),
    ("Storage", "External drives and storage solutions"),
    ("Audio", "Headphones, speakers, and audio gear"),
]

SUPPLIERS = [
    ("TechSource Global", "Sarah Chen", "sarah@techsource.com", "+1-555-0101", "1200 Innovation Blvd, San Jose, CA", 5),
    ("OfficeMax Wholesale", "James Wilson", "james@officemax.com", "+1-555-0102", "450 Commerce St, Dallas, TX", 7),
    ("NetGear Direct", "Maria Garcia", "maria@netgear.com", "+1-555-0103", "88 Network Lane, Austin, TX", 10),
    ("DataVault Inc", "Robert Kim", "robert@datavault.com", "+1-555-0104", "300 Storage Ave, Seattle, WA", 14),
    ("SoundWave Electronics", "Emily Brown", "emily@soundwave.com", "+1-555-0105", "75 Audio Park, Nashville, TN", 8),
]

PRODUCTS = [
    ("ELEC-001", "Wireless Mouse", "Electronics", "TechSource Global", 29.99, 12.50, 85, 15, 200, 25, 50, 5),
    ("ELEC-002", "Mechanical Keyboard", "Electronics", "TechSource Global", 89.99, 45.00, 42, 10, 100, 20, 30, 5),
    ("ELEC-003", "USB-C Hub 7-in-1", "Electronics", "TechSource Global", 49.99, 22.00, 120, 20, 300, 30, 60, 5),
    ("ELEC-004", "Laptop Stand", "Electronics", "TechSource Global", 39.99, 18.00, 65, 15, 150, 20, 40, 7),
    ("ELEC-005", "27-inch Monitor", "Electronics", "TechSource Global", 299.99, 180.00, 18, 5, 50, 10, 15, 10),
    ("ELEC-006", "Webcam HD 1080p", "Electronics", "TechSource Global", 59.99, 28.00, 55, 10, 120, 15, 30, 5),
    ("OFF-001", "Ergonomic Desk Chair", "Office Supplies", "OfficeMax Wholesale", 249.99, 130.00, 12, 3, 30, 5, 10, 7),
    ("OFF-002", "Standing Desk Converter", "Office Supplies", "OfficeMax Wholesale", 179.99, 95.00, 8, 2, 25, 5, 8, 7),
    ("OFF-003", "Document Organizer", "Office Supplies", "OfficeMax Wholesale", 24.99, 8.00, 200, 30, 500, 50, 100, 7),
    ("OFF-004", "Whiteboard Markers Set", "Office Supplies", "OfficeMax Wholesale", 14.99, 4.50, 350, 50, 800, 80, 150, 7),
    ("OFF-005", "Desk Lamp LED", "Office Supplies", "OfficeMax Wholesale", 34.99, 15.00, 45, 10, 100, 15, 30, 7),
    ("NET-001", "WiFi 6 Router", "Networking", "NetGear Direct", 129.99, 65.00, 28, 5, 60, 10, 20, 10),
    ("NET-002", "Ethernet Cable Cat6 10ft", "Networking", "NetGear Direct", 12.99, 3.50, 500, 100, 1000, 150, 200, 10),
    ("NET-003", "Network Switch 8-Port", "Networking", "NetGear Direct", 49.99, 25.00, 35, 8, 80, 12, 25, 10),
    ("NET-004", "Mesh WiFi Extender", "Networking", "NetGear Direct", 79.99, 40.00, 22, 5, 50, 8, 15, 10),
    ("NET-005", "Fiber Optic Patch Cable", "Networking", "NetGear Direct", 19.99, 8.00, 3, 10, 200, 20, 50, 10),
    ("STO-001", "External SSD 1TB", "Storage", "DataVault Inc", 89.99, 55.00, 40, 8, 100, 12, 25, 14),
    ("STO-002", "External HDD 4TB", "Storage", "DataVault Inc", 99.99, 60.00, 25, 5, 60, 8, 15, 14),
    ("STO-003", "USB Flash Drive 128GB", "Storage", "DataVault Inc", 19.99, 8.00, 180, 30, 400, 40, 80, 14),
    ("STO-004", "NAS Enclosure 2-Bay", "Storage", "DataVault Inc", 159.99, 90.00, 0, 3, 20, 5, 8, 14),
    ("STO-005", "SD Card 256GB", "Storage", "DataVault Inc", 34.99, 18.00, 95, 20, 250, 25, 50, 14),
    ("AUD-001", "Wireless Headphones", "Audio", "SoundWave Electronics", 79.99, 40.00, 60, 10, 150, 15, 30, 8),
    ("AUD-002", "Bluetooth Speaker", "Audio", "SoundWave Electronics", 49.99, 22.00, 75, 15, 180, 20, 40, 8),
    ("AUD-003", "USB Microphone", "Audio", "SoundWave Electronics", 69.99, 35.00, 30, 5, 80, 8, 20, 8),
    ("AUD-004", "Studio Monitor Speakers", "Audio", "SoundWave Electronics", 199.99, 110.00, 8, 2, 20, 4, 6, 8),
]

USERS = [
    ("admin@foresight.local", "System Administrator", "Admin@12345", "admin"),
    ("manager@foresight.local", "Inventory Manager", "Manager@12345", "manager"),
    ("testuser@example.com", "Test User", "Password@12345", "admin"),
]


def seed():
    init_db()
    db = SessionLocal()

    try:
        if db.query(User).count() > 0:
            print("Database already seeded. Skipping.")
            return

        roles = {}
        for name, desc in [("admin", "Full system access"), ("manager", "Inventory and sales management"), ("user", "Standard user access")]:
            role = Role(name=name, description=desc)
            db.add(role)
            db.flush()
            roles[name] = role

        for email, name, password, role_name in USERS:
            db.add(User(
                email=email,
                full_name=name,
                hashed_password=get_password_hash(password),
                role_id=roles[role_name].id,
            ))

        cat_map = {}
        for name, desc in CATEGORIES:
            cat = Category(name=name, description=desc)
            db.add(cat)
            db.flush()
            cat_map[name] = cat

        sup_map = {}
        for name, contact, email, phone, address, lead_time in SUPPLIERS:
            sup = Supplier(
                name=name, contact_person=contact, email=email,
                phone=phone, address=address, lead_time_days=lead_time,
            )
            db.add(sup)
            db.flush()
            sup_map[name] = sup

        product_map = {}
        for sku, name, cat_name, sup_name, price, cost, stock, min_s, max_s, reorder_pt, reorder_qty, lead_time in PRODUCTS:
            product = Product(
                sku=sku, name=name,
                description=f"High-quality {name.lower()} for professional use.",
                category_id=cat_map[cat_name].id,
                supplier_id=sup_map[sup_name].id,
                unit_price=price, cost_price=cost,
                current_stock=stock, minimum_stock=min_s, maximum_stock=max_s,
                reorder_point=reorder_pt, reorder_quantity=reorder_qty,
                lead_time_days=lead_time,
            )
            db.add(product)
            db.flush()
            db.add(Inventory(product_id=product.id, quantity=stock))
            product_map[sku] = product

        db.commit()

        # Generate historical sales (90 days)
        print("Generating historical sales data...")
        products_list = list(product_map.values())
        now = datetime.now(timezone.utc)

        for day_offset in range(90, 0, -1):
            sale_date = now - timedelta(days=day_offset)
            num_sales = random.randint(2, 8)
            for _ in range(num_sales):
                sale_number = f"SALE-{sale_date.strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
                num_items = random.randint(1, 4)
                selected = random.sample(products_list, min(num_items, len(products_list)))
                sale = Sale(
                    sale_number=sale_number,
                    customer_name=random.choice(["Acme Corp", "TechStart Inc", "Global Retail", "Local Business", "Online Customer", None]),
                    sale_date=sale_date.replace(hour=random.randint(8, 18), minute=random.randint(0, 59)),
                )
                db.add(sale)
                db.flush()

                total_amount = 0.0
                total_units = 0
                for product in selected:
                    base_demand = max(1, int(90 - day_offset) // 10 + 1)
                    qty = random.randint(1, min(5, base_demand + 2))
                    line_total = float(product.unit_price) * qty
                    db.add(SalesItem(
                        sale_id=sale.id, product_id=product.id,
                        quantity=qty, unit_price=float(product.unit_price),
                        line_total=line_total,
                    ))
                    total_amount += line_total
                    total_units += qty

                sale.total_amount = total_amount
                sale.total_units = total_units

        db.commit()

        # Generate some inventory transactions
        for product in random.sample(products_list, 10):
            db.add(InventoryTransaction(
                product_id=product.id,
                transaction_type="incoming",
                quantity_change=random.randint(20, 100),
                quantity_before=product.current_stock,
                quantity_after=product.current_stock + random.randint(20, 100),
                reference="PO-SEED",
                notes="Initial stock replenishment",
            ))

        db.commit()

        # Generate alerts and recommendations
        print("Generating alerts and recommendations...")
        generate_alerts(db)
        generate_all_recommendations(db)

        # Generate forecasts for top products
        from app.ml.forecast_engine import generate_forecast
        from app.models.forecast import DemandForecast, ForecastResult

        top_products = products_list[:5]
        for product in top_products:
            sales_records = (
                db.query(SalesItem.quantity, Sale.sale_date)
                .join(Sale)
                .filter(SalesItem.product_id == product.id)
                .all()
            )
            records = [{"quantity": r.quantity, "sale_date": r.sale_date} for r in sales_records]
            result = generate_forecast(records, 30)
            forecast = DemandForecast(
                product_id=product.id,
                horizon_days=30,
                model_type=result["model_type"],
                confidence_score=result["confidence_score"],
                mae=result["mae"],
                rmse=result["rmse"],
                status=result["status"],
                notes=result["notes"],
            )
            db.add(forecast)
            db.flush()
            for r in result["results"]:
                db.add(ForecastResult(
                    forecast_id=forecast.id,
                    forecast_date=r["forecast_date"],
                    predicted_demand=r["predicted_demand"],
                    lower_bound=r.get("lower_bound"),
                    upper_bound=r.get("upper_bound"),
                    is_historical=r.get("is_historical", False),
                ))

        db.commit()
        print("Seed completed successfully!")
        print(f"  - {len(CATEGORIES)} categories")
        print(f"  - {len(SUPPLIERS)} suppliers")
        print(f"  - {len(PRODUCTS)} products")
        print(f"  - Historical sales generated")
        print(f"  - Demo users: admin@foresight.local / Admin@12345")
        print(f"  - Demo users: manager@foresight.local / Manager@12345")

    finally:
        db.close()


if __name__ == "__main__":
    seed()
