
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import models, schemas
from app.dependencies import get_db

router = APIRouter(
    prefix="/clients",
    tags=["Clients"]
)


# POST - Create Client
@router.post("/")
def create_client(
    client: schemas.ClientCreate,
    db: Session = Depends(get_db)
):
    new_client = models.Client(
        client_name=client.client_name,
        email=client.email,
        phone=client.phone
    )

    db.add(new_client)
    db.commit()
    db.refresh(new_client)

    return new_client


# GET - Get All Clients
@router.get("/")
def get_clients(db: Session = Depends(get_db)):
    clients = db.query(models.Client).all()
    return clients


# GET - Get Client by ID
@router.get("/{client_id}")
def get_client(
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

    return client


# PUT - Update Client
@router.put("/{client_id}")
def update_client(
    client_id: int,
    client: schemas.ClientCreate,
    db: Session = Depends(get_db)
):
    existing_client = db.query(models.Client).filter(
        models.Client.client_id == client_id
    ).first()

    if existing_client is None:
        raise HTTPException(
            status_code=404,
            detail="Client not found"
        )

    existing_client.client_name = client.client_name
    existing_client.email = client.email
    existing_client.phone = client.phone

    db.commit()
    db.refresh(existing_client)

    return existing_client


# DELETE - Delete Client
@router.delete("/{client_id}")
def delete_client(
    client_id: int,
    db: Session = Depends(get_db)
):
    existing_client = db.query(models.Client).filter(
        models.Client.client_id == client_id
    ).first()

    if existing_client is None:
        raise HTTPException(
            status_code=404,
            detail="Client not found"
        )

    db.delete(existing_client)
    db.commit()

    return {"message": "Client deleted successfully"}
