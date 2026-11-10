
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import models, schemas
from app.dependencies import get_db

router = APIRouter(
    prefix="/items",
    tags=["Items"]
)


# POST - Create Item
@router.post("/")
def create_item(
    item: schemas.ItemCreate,
    db: Session = Depends(get_db)
):
    new_item = models.Item(
        item_name=item.item_name,
        available_quantity=item.available_quantity,
        minimum_quantity=item.minimum_quantity,
        price=item.price,
        vendor_id=item.vendor_id
    )

    db.add(new_item)
    db.commit()
    db.refresh(new_item)

    return new_item


# GET - Get All Items
@router.get("/")
def get_items(db: Session = Depends(get_db)):
    items = db.query(models.Item).all()
    return items


# GET - Get Low Stock Items
@router.get("/low-stock")
def get_low_stock_items(db: Session = Depends(get_db)):
    items = db.query(models.Item).filter(
        models.Item.available_quantity <= models.Item.minimum_quantity
    ).all()

    return items


# GET - Get Item by ID
@router.get("/{item_id}")
def get_item(
    item_id: int,
    db: Session = Depends(get_db)
):
    item = db.query(models.Item).filter(
        models.Item.item_id == item_id
    ).first()

    if item is None:
        raise HTTPException(
            status_code=404,
            detail="Item not found"
        )

    return item


# PUT - Update Item
@router.put("/{item_id}")
def update_item(
    item_id: int,
    item: schemas.ItemCreate,
    db: Session = Depends(get_db)
):
    existing_item = db.query(models.Item).filter(
        models.Item.item_id == item_id
    ).first()

    if existing_item is None:
        raise HTTPException(
            status_code=404,
            detail="Item not found"
        )

    existing_item.item_name = item.item_name
    existing_item.available_quantity = item.available_quantity
    existing_item.minimum_quantity = item.minimum_quantity
    existing_item.price = item.price
    existing_item.vendor_id = item.vendor_id

    db.commit()
    db.refresh(existing_item)

    return existing_item


# DELETE - Delete Item
@router.delete("/{item_id}")
def delete_item(
    item_id: int,
    db: Session = Depends(get_db)
):
    existing_item = db.query(models.Item).filter(
        models.Item.item_id == item_id
    ).first()

    if existing_item is None:
        raise HTTPException(
            status_code=404,
            detail="Item not found"
        )

    db.delete(existing_item)
    db.commit()

    return {"message": "Item deleted successfully"}
