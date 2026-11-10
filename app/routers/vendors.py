
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import models, schemas
from app.dependencies import get_db

router = APIRouter(
    prefix="/vendors",
    tags=["Vendors"]
)


# POST - Create Vendor
@router.post("/")
def create_vendor(
    vendor: schemas.VendorCreate,
    db: Session = Depends(get_db)
):
    new_vendor = models.Vendor(
        vendor_name=vendor.vendor_name,
        email=vendor.email,
        phone=vendor.phone
    )

    db.add(new_vendor)
    db.commit()
    db.refresh(new_vendor)

    return new_vendor


# GET - Get All Vendors
@router.get("/")
def get_vendors(db: Session = Depends(get_db)):
    vendors = db.query(models.Vendor).all()
    return vendors


# GET - Get Vendor By ID
@router.get("/{vendor_id}")
def get_vendor(
    vendor_id: int,
    db: Session = Depends(get_db)
):
    vendor = db.query(models.Vendor).filter(
        models.Vendor.vendor_id == vendor_id
    ).first()

    if vendor is None:
        raise HTTPException(
            status_code=404,
            detail="Vendor not found"
        )

    return vendor


# PUT - Update Vendor
@router.put("/{vendor_id}")
def update_vendor(
    vendor_id: int,
    vendor: schemas.VendorCreate,
    db: Session = Depends(get_db)
):
    existing_vendor = db.query(models.Vendor).filter(
        models.Vendor.vendor_id == vendor_id
    ).first()

    if existing_vendor is None:
        raise HTTPException(
            status_code=404,
            detail="Vendor not found"
        )

    existing_vendor.vendor_name = vendor.vendor_name
    existing_vendor.email = vendor.email
    existing_vendor.phone = vendor.phone

    db.commit()
    db.refresh(existing_vendor)

    return existing_vendor


# DELETE - Delete Vendor
@router.delete("/{vendor_id}")
def delete_vendor(
    vendor_id: int,
    db: Session = Depends(get_db)
):
    existing_vendor = db.query(models.Vendor).filter(
        models.Vendor.vendor_id == vendor_id
    ).first()

    if existing_vendor is None:
        raise HTTPException(
            status_code=404,
            detail="Vendor not found"
        )

    db.delete(existing_vendor)
    db.commit()

    return {"message": "Vendor deleted successfully"}
