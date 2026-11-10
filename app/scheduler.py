from apscheduler.schedulers.background import BackgroundScheduler
from app.database import SessionLocal
from app import models

scheduler = BackgroundScheduler()


def check_low_stock():
    db = SessionLocal()

    try:
        low_stock_items = db.query(models.Item).filter(
            models.Item.available_quantity <= models.Item.minimum_quantity
        ).all()

        for item in low_stock_items:

            if not item.vendor_id:
                continue

            existing_request = db.query(
                models.ReplenishmentRequest
            ).filter(
                models.ReplenishmentRequest.item_id == item.item_id,
                models.ReplenishmentRequest.status == "PENDING"
            ).first()

            if existing_request:
                continue

            target_quantity = item.minimum_quantity * 2

            requested_quantity = (
                target_quantity - item.available_quantity
            )

            if requested_quantity <= 0:
                continue

            new_request = models.ReplenishmentRequest(
                item_id=item.item_id,
                vendor_id=item.vendor_id,
                requested_quantity=requested_quantity
            )

            db.add(new_request)

        db.commit()

        print("Automatic low-stock check completed!")

    except Exception as e:
        db.rollback()
        print("Low-stock check failed:", e)

    finally:
        db.close()


def start_scheduler():
    if not scheduler.running:
        scheduler.add_job(
            check_low_stock,
            trigger="interval",
            hours=2,
            id="low_stock_check",
            replace_existing=True
        )

        scheduler.start()
        print("Inventory scheduler started!")


def stop_scheduler():
    if scheduler.running:
        scheduler.shutdown()