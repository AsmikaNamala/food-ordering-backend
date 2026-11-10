from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app import models, schemas
from app.dependencies import get_db
from datetime import datetime

router = APIRouter(
    prefix="/replenishment",
    tags=["Replenishment"]
)


# POST - Create Replenishment Request
@router.post("/")
def create_replenishment_request(
    request: schemas.ReplenishmentRequestCreate,
    db: Session = Depends(get_db)
):
    item = db.query(models.Item).filter(
        models.Item.item_id == request.item_id
    ).first()

    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    if item.available_quantity > item.minimum_quantity:
        raise HTTPException(
            status_code=400,
            detail="Item stock is sufficient"
        )

    existing_request = db.query(models.ReplenishmentRequest).filter(
        models.ReplenishmentRequest.item_id == item.item_id,
        models.ReplenishmentRequest.status == "PENDING"
    ).first()

    if existing_request:
        raise HTTPException(
            status_code=400,
            detail="Pending replenishment request already exists"
        )

    if not item.vendor_id:
        raise HTTPException(
            status_code=400,
            detail="No vendor assigned to this item"
        )

    target_quantity = item.minimum_quantity * 2
    requested_quantity = target_quantity - item.available_quantity

    new_request = models.ReplenishmentRequest(
        item_id=item.item_id,
        vendor_id=item.vendor_id,
        requested_quantity=requested_quantity
    )

    db.add(new_request)
    db.commit()
    db.refresh(new_request)

    return new_request
# POST - Vendor Approves or Rejects Replenishment
@router.post("/{request_id}/review")
def review_replenishment_request(
    request_id: int,
    review: schemas.ReplenishmentReview,
    db: Session = Depends(get_db)
):
    replenishment = db.query(
        models.ReplenishmentRequest
    ).filter(
        models.ReplenishmentRequest.request_id == request_id
    ).first()

    if not replenishment:
        raise HTTPException(
            status_code=404,
            detail="Replenishment request not found"
        )

    if replenishment.status != "PENDING":
        raise HTTPException(
            status_code=400,
            detail="Request has already been reviewed"
        )

    if review.approved:
        item = db.query(models.Item).filter(
            models.Item.item_id == replenishment.item_id
        ).first()

        if not item:
            raise HTTPException(
                status_code=404,
                detail="Item not found"
            )

        item.available_quantity += replenishment.requested_quantity
        replenishment.status = "APPROVED"

    else:
        replenishment.status = "REJECTED"

    replenishment.reviewed_at = datetime.now()

    db.commit()
    db.refresh(replenishment)

    return {
        "message": "Replenishment request reviewed successfully",
        "request_id": replenishment.request_id,
        "status": replenishment.status,
        "item_id": replenishment.item_id
    }