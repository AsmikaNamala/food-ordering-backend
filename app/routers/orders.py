
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import models, schemas
from app.dependencies import get_db


router = APIRouter(
    prefix="/orders",
    tags=["Orders"]
)


# --------------------------------------------------
# CREATE ORDER
# --------------------------------------------------

@router.post("/")
def create_order(
    order: schemas.OrderCreate,
    db: Session = Depends(get_db)
):
    try:
        # 1. Check whether client exists
        client = db.query(models.Client).filter(
            models.Client.client_id == order.client_id
        ).first()

        if client is None:
            raise HTTPException(
                status_code=404,
                detail="Client not found"
            )

        # 2. Check whether order contains items
        if not order.items:
            raise HTTPException(
                status_code=400,
                detail="Order must contain at least one item"
            )

        # 3. Combine duplicate item IDs and validate quantities
        item_quantities = {}

        for order_item in order.items:
            if order_item.quantity <= 0:
                raise HTTPException(
                    status_code=400,
                    detail="Quantity must be greater than zero"
                )

            if order_item.item_id not in item_quantities:
                item_quantities[order_item.item_id] = 0

            item_quantities[order_item.item_id] += order_item.quantity

        # 4. Lock requested items in consistent order
        item_ids = sorted(item_quantities.keys())

        locked_items = db.query(models.Item).filter(
            models.Item.item_id.in_(item_ids)
        ).order_by(
            models.Item.item_id
        ).with_for_update().all()

        items_by_id = {
            item.item_id: item
            for item in locked_items
        }

        # 5. Validate stock and calculate total
        total_amount = 0

        for item_id, quantity in item_quantities.items():
            item = items_by_id.get(item_id)

            if item is None:
                raise HTTPException(
                    status_code=404,
                    detail=f"Item {item_id} not found"
                )

            if item.available_quantity < quantity:
                raise HTTPException(
                    status_code=400,
                    detail=f"Not enough stock for {item.item_name}"
                )

            total_amount += item.price * quantity

        # 6. Create order
        new_order = models.Order(
            client_id=order.client_id,
            total_amount=total_amount
        )

        db.add(new_order)
        db.flush()

        # 7. Add order items and reduce stock
        for item_id, quantity in item_quantities.items():
            item = items_by_id[item_id]

            item.available_quantity -= quantity

            new_order_item = models.OrderItem(
                order_id=new_order.order_id,
                item_id=item.item_id,
                quantity=quantity,
                price=item.price
            )

            db.add(new_order_item)

        # 8. Commit transaction
        db.commit()
        db.refresh(new_order)

        return new_order

    except Exception:
        db.rollback()
        raise


# --------------------------------------------------
# GET ALL ORDERS
# --------------------------------------------------

@router.get("/")
def get_orders(db: Session = Depends(get_db)):

    orders = db.query(models.Order).order_by(
        models.Order.created_at.desc()
    ).all()

    return orders


# --------------------------------------------------
# GET ORDER HISTORY BY CLIENT ID
# --------------------------------------------------

@router.get("/client/{client_id}")
def get_client_order_history(
    client_id: int,
    db: Session = Depends(get_db)
):
    client = db.query(models.Client).filter(
        models.Client.client_id == client_id
    ).first()

    if client is None:
        raise HTTPException(
            status_code=404,
            detail="Client not found"
        )

    orders = db.query(models.Order).filter(
        models.Order.client_id == client_id
    ).order_by(
        models.Order.created_at.desc()
    ).all()

    history = []

    for order in orders:

        order_items = db.query(models.OrderItem).filter(
            models.OrderItem.order_id == order.order_id
        ).order_by(
            models.OrderItem.item_id
        ).all()

        items = []

        for order_item in order_items:

            item = db.query(models.Item).filter(
                models.Item.item_id == order_item.item_id
            ).first()

            items.append({
                "item_id": order_item.item_id,
                "item_name": item.item_name if item else "Deleted item",
                "quantity": order_item.quantity,
                "price": order_item.price,
                "subtotal": order_item.price * order_item.quantity
            })

        history.append({
            "order_id": order.order_id,
            "client_id": order.client_id,
            "items": items,
            "total_amount": order.total_amount,
            "order_status": order.order_status,
            "payment_status": order.payment_status,
            "created_at": order.created_at
        })

    return {
        "client_id": client_id,
        "client_name": client.client_name,
        "total_orders": len(history),
        "orders": history
    }


# --------------------------------------------------
# GET COMPLETE ORDER DETAILS
# --------------------------------------------------

@router.get("/{order_id}/details")
def get_order_details(
    order_id: int,
    db: Session = Depends(get_db)
):
    order = db.query(models.Order).filter(
        models.Order.order_id == order_id
    ).first()

    if order is None:
        raise HTTPException(
            status_code=404,
            detail="Order not found"
        )

    order_items = db.query(models.OrderItem).filter(
        models.OrderItem.order_id == order.order_id
    ).order_by(
        models.OrderItem.item_id
    ).all()

    items = []

    for order_item in order_items:

        item = db.query(models.Item).filter(
            models.Item.item_id == order_item.item_id
        ).first()

        items.append({
            "item_id": order_item.item_id,
            "item_name": item.item_name if item else "Deleted item",
            "quantity": order_item.quantity,
            "price": order_item.price,
            "subtotal": order_item.price * order_item.quantity
        })

    return {
        "order_id": order.order_id,
        "client_id": order.client_id,
        "items": items,
        "total_amount": order.total_amount,
        "order_status": order.order_status,
        "payment_status": order.payment_status,
        "created_at": order.created_at
    }


# --------------------------------------------------
# GET ORDER BY ID
# --------------------------------------------------

@router.get("/{order_id}")
def get_order(
    order_id: int,
    db: Session = Depends(get_db)
):
    order = db.query(models.Order).filter(
        models.Order.order_id == order_id
    ).first()

    if order is None:
        raise HTTPException(
            status_code=404,
            detail="Order not found"
        )

    return order


# --------------------------------------------------
# DUMMY PAYMENT API
# --------------------------------------------------

@router.post("/{order_id}/payment")
def make_payment(
    order_id: int,
    payment: schemas.PaymentRequest,
    db: Session = Depends(get_db)
):
    try:
        order = db.query(models.Order).filter(
            models.Order.order_id == order_id
        ).with_for_update().first()

        if order is None:
            raise HTTPException(
                status_code=404,
                detail="Order not found"
            )

        if order.payment_status != "PENDING":
            raise HTTPException(
                status_code=400,
                detail="Payment already processed"
            )

        if payment.payment_success:

            # Payment successful
            order.payment_status = "SUCCESS"
            order.order_status = "CONFIRMED"

        else:

            # Payment failed: restore inventory
            order_items = db.query(models.OrderItem).filter(
                models.OrderItem.order_id == order_id
            ).order_by(
                models.OrderItem.item_id
            ).all()

            for order_item in order_items:

                item = db.query(models.Item).filter(
                    models.Item.item_id == order_item.item_id
                ).with_for_update().first()

                if item is not None:
                    item.available_quantity += order_item.quantity

            order.payment_status = "FAILED"
            order.order_status = "CANCELLED"

        db.commit()
        db.refresh(order)

        return {
            "message": "Payment processed",
            "order_id": order.order_id,
            "payment_status": order.payment_status,
            "order_status": order.order_status,
            "total_amount": order.total_amount
        }

    except Exception:
        db.rollback()
        raise


# --------------------------------------------------
# CANCEL ORDER
# --------------------------------------------------

@router.post("/{order_id}/cancel")
def cancel_order(
    order_id: int,
    db: Session = Depends(get_db)
):
    try:
        order = db.query(models.Order).filter(
            models.Order.order_id == order_id
        ).with_for_update().first()

        if order is None:
            raise HTTPException(
                status_code=404,
                detail="Order not found"
            )

        if (
            order.order_status != "PENDING"
            or order.payment_status != "PENDING"
        ):
            raise HTTPException(
                status_code=400,
                detail="Order cannot be cancelled"
            )

        # Restore inventory
        order_items = db.query(models.OrderItem).filter(
            models.OrderItem.order_id == order_id
        ).order_by(
            models.OrderItem.item_id
        ).all()

        for order_item in order_items:

            item = db.query(models.Item).filter(
                models.Item.item_id == order_item.item_id
            ).with_for_update().first()

            if item is not None:
                item.available_quantity += order_item.quantity

        order.order_status = "CANCELLED"
        order.payment_status = "CANCELLED"

        db.commit()
        db.refresh(order)

        return {
            "message": "Order cancelled successfully",
            "order_id": order.order_id,
            "order_status": order.order_status,
            "payment_status": order.payment_status
        }

    except Exception:
        db.rollback()
        raise
