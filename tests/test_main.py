import pytest
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from app import models
from fastapi.testclient import TestClient
from app.main import app
from uuid import uuid4
client = TestClient(app)


def test_health_check():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_home():
    response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {
        "message": "Welcome to Food Ordering Backend"
    }
def test_get_vendors():
    response = client.get("/vendors/")

    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_get_vendor_not_found():
    response = client.get("/vendors/999999")

    assert response.status_code == 404
def test_get_client_not_found():
    response = client.get("/clients/999999")
    assert response.status_code == 404
def test_get_item_not_found():
    response = client.get("/items/999999")

    assert response.status_code == 404
# ORDER TESTS

def test_get_orders():
    response = client.get("/orders/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_get_order_not_found():
    response = client.get("/orders/999999")
    assert response.status_code == 404


def test_get_order_details_not_found():
    response = client.get("/orders/999999/details")
    assert response.status_code == 404


def test_get_client_order_history_not_found():
    response = client.get("/orders/client/999999")
    assert response.status_code == 404
def test_payment_order_not_found():
    response = client.post(
        "/orders/999999/payment",
        json={"payment_success": True}
    )

    assert response.status_code == 404


def test_cancel_order_not_found():
    response = client.post("/orders/999999/cancel")

    assert response.status_code == 404
def test_order_zero_quantity():
    response = client.post(
        "/orders/",
        json={
            "client_id": 2,
            "items": [
                {"item_id": 1, "quantity": 0}
            ]
        }
    )
    assert response.status_code == 422


def test_order_negative_quantity():
    response = client.post(
        "/orders/",
        json={
            "client_id": 2,
            "items": [
                {"item_id": 1, "quantity": -5}
            ]
        }
    )
    assert response.status_code == 422


def test_order_empty_items():
    response = client.post(
        "/orders/",
        json={
            "client_id": 2,
            "items": []
        }
    )
    assert response.status_code == 422


def test_order_invalid_item_id():
    response = client.post(
        "/orders/",
        json={
            "client_id": 2,
            "items": [
                {"item_id": 0, "quantity": 2}
            ]
        }
    )
    assert response.status_code == 422
# @pytest.fixture
# def order_test_data():

#     db = TestingSessionLocal()

#     unique_id = str(uuid4())

#     test_client = models.Client(
#         client_name="Test Client",
#         email=f"test_{unique_id}@example.com"
#     )

#     test_item = models.Item(
#         item_name=f"Test Burger {unique_id}",
#         available_quantity=10,
#         minimum_quantity=2,
#         price=100
#     )

#     db.add(test_client)
#     db.add(test_item)
#     db.commit()

#     db.refresh(test_client)
#     db.refresh(test_item)

#     data = {
#         "client_id": test_client.client_id,
#         "item_id": test_item.item_id
#     }

#     try:
#         yield data

#     finally:
#         orders = db.query(models.Order).filter(
#             models.Order.client_id == test_client.client_id
#         ).all()

#         order_ids = [order.order_id for order in orders]

#         if order_ids:
#             db.query(models.OrderItem).filter(
#                 models.OrderItem.order_id.in_(order_ids)
#             ).delete(synchronize_session=False)

#             db.query(models.Order).filter(
#                 models.Order.order_id.in_(order_ids)
#             ).delete(synchronize_session=False)

#         db.query(models.Item).filter(
#             models.Item.item_id == test_item.item_id
#         ).delete()

#         db.query(models.Client).filter(
#             models.Client.client_id == test_client.client_id
#         ).delete()

#         db.commit()
#         db.close()
def test_create_order_success(order_test_data):

    response = client.post(
        "/orders/",
        json={
            "client_id": order_test_data["client_id"],
            "items": [
                {
                    "item_id": order_test_data["item_id"],
                    "quantity": 2
                }
            ]
        }
    )

    assert response.status_code == 200

    data = response.json()

    # Check order details
    assert data["client_id"] == order_test_data["client_id"]
    assert data["total_amount"] == "200.00" or data["total_amount"] == 200
    assert data["order_status"] == "PENDING"
    assert data["payment_status"] == "PENDING"

    # Check stock reduction
    db = order_test_data["db"]
    db.expire_all()

    item = db.query(models.Item).filter(
        models.Item.item_id == order_test_data["item_id"]
    ).first()

    assert item.available_quantity == 8
def test_create_order_insufficient_stock(order_test_data):

    response = client.post(
        "/orders/",
        json={
            "client_id": order_test_data["client_id"],
            "items": [
                {
                    "item_id": order_test_data["item_id"],
                    "quantity": 11
                }
            ]
        }
    )

    assert response.status_code == 400

    # Verify stock remains unchanged
    db = order_test_data["db"]
    db.expire_all()

    item = db.query(models.Item).filter(
        models.Item.item_id == order_test_data["item_id"]
    ).first()

    assert item.available_quantity == 10
def test_create_order_duplicate_items(order_test_data):

    response = client.post(
        "/orders/",
        json={
            "client_id": order_test_data["client_id"],
            "items": [
                {
                    "item_id": order_test_data["item_id"],
                    "quantity": 3
                },
                {
                    "item_id": order_test_data["item_id"],
                    "quantity": 4
                }
            ]
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total_amount"] == "700.00" or data["total_amount"] == 700

    # Verify stock
    db = order_test_data["db"]
    db.expire_all()

    item = db.query(models.Item).filter(
        models.Item.item_id == order_test_data["item_id"]
    ).first()

    assert item.available_quantity == 3
def test_payment_success(order_test_data):

    # First create an order
    response = client.post(
        "/orders/",
        json={
            "client_id": order_test_data["client_id"],
            "items": [
                {
                    "item_id": order_test_data["item_id"],
                    "quantity": 2
                }
            ]
        }
    )

    assert response.status_code == 200

    order_id = response.json()["order_id"]

    # Process successful payment
    payment_response = client.post(
        f"/orders/{order_id}/payment",
        json={
            "payment_success": True
        }
    )

    assert payment_response.status_code == 200

    payment_data = payment_response.json()

    assert payment_data["payment_status"] == "SUCCESS"
    assert payment_data["order_status"] == "CONFIRMED"

    # Verify stock is still 8 (not deducted again)
    db = order_test_data["db"]
    db.expire_all()

    item = db.query(models.Item).filter(
        models.Item.item_id == order_test_data["item_id"]
    ).first()

    assert item.available_quantity == 8
def test_payment_failure(order_test_data):

    # Create an order
    response = client.post(
        "/orders/",
        json={
            "client_id": order_test_data["client_id"],
            "items": [
                {
                    "item_id": order_test_data["item_id"],
                    "quantity": 2
                }
            ]
        }
    )

    assert response.status_code == 200

    order_id = response.json()["order_id"]

    # Process failed payment
    payment_response = client.post(
        f"/orders/{order_id}/payment",
        json={
            "payment_success": False
        }
    )

    assert payment_response.status_code == 200

    payment_data = payment_response.json()

    assert payment_data["payment_status"] == "FAILED"
    assert payment_data["order_status"] == "CANCELLED"

    # Verify stock is restored to 10
    db = order_test_data["db"]
    db.expire_all()

    item = db.query(models.Item).filter(
        models.Item.item_id == order_test_data["item_id"]
    ).first()

    assert item.available_quantity == 10
def test_cancel_order_success(order_test_data):

    # Create an order
    response = client.post(
        "/orders/",
        json={
            "client_id": order_test_data["client_id"],
            "items": [
                {
                    "item_id": order_test_data["item_id"],
                    "quantity": 2
                }
            ]
        }
    )

    assert response.status_code == 200

    order_id = response.json()["order_id"]

    # Cancel the order
    cancel_response = client.post(
        f"/orders/{order_id}/cancel"
    )

    assert cancel_response.status_code == 200

    cancel_data = cancel_response.json()

    assert cancel_data["order_status"] == "CANCELLED"
    assert cancel_data["payment_status"] == "CANCELLED"

    # Verify stock is restored
    db = order_test_data["db"]
    db.expire_all()

    item = db.query(models.Item).filter(
        models.Item.item_id == order_test_data["item_id"]
    ).first()

    assert item.available_quantity == 10
def test_cancel_paid_order(order_test_data):

    # Create an order
    response = client.post(
        "/orders/",
        json={
            "client_id": order_test_data["client_id"],
            "items": [
                {
                    "item_id": order_test_data["item_id"],
                    "quantity": 2
                }
            ]
        }
    )

    assert response.status_code == 200
    order_id = response.json()["order_id"]

    # Complete payment
    payment_response = client.post(
        f"/orders/{order_id}/payment",
        json={"payment_success": True}
    )

    assert payment_response.status_code == 200

    # Try cancelling the paid order
    cancel_response = client.post(
        f"/orders/{order_id}/cancel"
    )

    assert cancel_response.status_code == 400
    assert cancel_response.json()["detail"] == "Order cannot be cancelled"

    # Verify stock remains deducted
    db = order_test_data["db"]
    db.expire_all()

    item = db.query(models.Item).filter(
        models.Item.item_id == order_test_data["item_id"]
    ).first()

    assert item.available_quantity == 8
def test_duplicate_payment(order_test_data):

    # Create order
    response = client.post(
        "/orders/",
        json={
            "client_id": order_test_data["client_id"],
            "items": [
                {
                    "item_id": order_test_data["item_id"],
                    "quantity": 2
                }
            ]
        }
    )

    assert response.status_code == 200
    order_id = response.json()["order_id"]

    # First payment
    first_payment = client.post(
        f"/orders/{order_id}/payment",
        json={"payment_success": True}
    )

    assert first_payment.status_code == 200

    # Attempt second payment
    second_payment = client.post(
        f"/orders/{order_id}/payment",
        json={"payment_success": True}
    )

    assert second_payment.status_code == 400
    assert second_payment.json()["detail"] == "Payment already processed"
def test_duplicate_cancellation(order_test_data):

    # Create order
    response = client.post(
        "/orders/",
        json={
            "client_id": order_test_data["client_id"],
            "items": [
                {
                    "item_id": order_test_data["item_id"],
                    "quantity": 2
                }
            ]
        }
    )

    assert response.status_code == 200
    order_id = response.json()["order_id"]

    # First cancellation
    first_cancel = client.post(
        f"/orders/{order_id}/cancel"
    )

    assert first_cancel.status_code == 200

    # Second cancellation
    second_cancel = client.post(
        f"/orders/{order_id}/cancel"
    )

    assert second_cancel.status_code == 400
    assert second_cancel.json()["detail"] == "Order cannot be cancelled"

    # Verify stock was restored only once
    db = order_test_data["db"]
    db.expire_all()

    item = db.query(models.Item).filter(
        models.Item.item_id == order_test_data["item_id"]
    ).first()

    assert item.available_quantity == 10
def test_client_order_history(order_test_data):
    client_id = order_test_data["client_id"]
    item_id = order_test_data["item_id"]

    # Create first order
    response1 = client.post("/orders/", json={
        "client_id": client_id,
        "items": [
            {"item_id": item_id, "quantity": 1}
        ]
    })

    # Create second order
    response2 = client.post("/orders/", json={
        "client_id": client_id,
        "items": [
            {"item_id": item_id, "quantity": 2}
        ]
    })

    assert response1.status_code == 200
    assert response2.status_code == 200

    # Get client's order history
    response = client.get(f"/orders/client/{client_id}")

    assert response.status_code == 200

    data = response.json()

    assert data["client_id"] == client_id
    assert data["total_orders"] == 2
    assert len(data["orders"]) == 2
def test_order_details_success(order_test_data):
    client_id = order_test_data["client_id"]
    item_id = order_test_data["item_id"]

    # Create an order
    create_response = client.post("/orders/", json={
        "client_id": client_id,
        "items": [
            {"item_id": item_id, "quantity": 2}
        ]
    })

    assert create_response.status_code == 200

    order_id = create_response.json()["order_id"]

    # Get complete order details
    response = client.get(f"/orders/{order_id}/details")

    assert response.status_code == 200

    data = response.json()

    assert data["order_id"] == order_id
    assert data["client_id"] == client_id
    assert data["total_amount"] == 200
    assert len(data["items"]) == 1
    assert data["items"][0]["quantity"] == 2
    assert data["items"][0]["subtotal"] == 200
def test_get_order_success(order_test_data):
    response = client.post("/orders/", json={
        "client_id": order_test_data["client_id"],
        "items": [
            {
                "item_id": order_test_data["item_id"],
                "quantity": 2
            }
        ]
    })

    assert response.status_code == 200

    order_id = response.json()["order_id"]

    response = client.get(f"/orders/{order_id}")

    assert response.status_code == 200
    assert response.json()["order_id"] == order_id
    assert response.json()["total_amount"] == 200
def test_create_order_multiple_items(order_test_data):
    response = client.post("/orders/", json={
        "client_id": order_test_data["client_id"],
        "items": [
            {
                "item_id": order_test_data["item_id"],
                "quantity": 2
            },
            {
                "item_id": order_test_data["item2_id"],
                "quantity": 3
            }
        ]
    })

    assert response.status_code == 200

    data = response.json()

    # Total = (2 × 100) + (3 × 200) = 800
    assert data["total_amount"] == 800

    db = order_test_data["db"]
    db.expire_all()

    burger = db.query(models.Item).filter(
        models.Item.item_id == order_test_data["item_id"]
    ).first()

    pizza = db.query(models.Item).filter(
        models.Item.item_id == order_test_data["item2_id"]
    ).first()

    assert burger.available_quantity == 8
    assert pizza.available_quantity == 12
def test_payment_failure_multiple_items(order_test_data):
    response = client.post("/orders/", json={
        "client_id": order_test_data["client_id"],
        "items": [
            {
                "item_id": order_test_data["item_id"],
                "quantity": 2
            },
            {
                "item_id": order_test_data["item2_id"],
                "quantity": 3
            }
        ]
    })

    assert response.status_code == 200
    order_id = response.json()["order_id"]

    payment_response = client.post(
        f"/orders/{order_id}/payment",
        json={"payment_success": False}
    )

    assert payment_response.status_code == 200
    assert payment_response.json()["payment_status"] == "FAILED"
    assert payment_response.json()["order_status"] == "CANCELLED"

    db = order_test_data["db"]
    db.expire_all()

    burger = db.query(models.Item).filter(
        models.Item.item_id == order_test_data["item_id"]
    ).first()

    pizza = db.query(models.Item).filter(
        models.Item.item_id == order_test_data["item2_id"]
    ).first()

    assert burger.available_quantity == 10
    assert pizza.available_quantity == 15
def test_cancel_order_multiple_items(order_test_data):
    response = client.post("/orders/", json={
        "client_id": order_test_data["client_id"],
        "items": [
            {
                "item_id": order_test_data["item_id"],
                "quantity": 2
            },
            {
                "item_id": order_test_data["item2_id"],
                "quantity": 3
            }
        ]
    })

    assert response.status_code == 200
    order_id = response.json()["order_id"]

    cancel_response = client.post(
        f"/orders/{order_id}/cancel"
    )

    assert cancel_response.status_code == 200
    assert cancel_response.json()["order_status"] == "CANCELLED"

    db = order_test_data["db"]
    db.expire_all()

    burger = db.query(models.Item).filter(
        models.Item.item_id == order_test_data["item_id"]
    ).first()

    pizza = db.query(models.Item).filter(
        models.Item.item_id == order_test_data["item2_id"]
    ).first()

    assert burger.available_quantity == 10
    assert pizza.available_quantity == 15
def test_multiple_items_insufficient_stock(order_test_data):
    response = client.post("/orders/", json={
        "client_id": order_test_data["client_id"],
        "items": [
            {
                "item_id": order_test_data["item_id"],
                "quantity": 2
            },
            {
                "item_id": order_test_data["item2_id"],
                "quantity": 16
            }
        ]
    })

    assert response.status_code == 400

    db = order_test_data["db"]
    db.expire_all()

    burger = db.query(models.Item).filter(
        models.Item.item_id == order_test_data["item_id"]
    ).first()

    pizza = db.query(models.Item).filter(
        models.Item.item_id == order_test_data["item2_id"]
    ).first()

    # Neither item's stock should change
    assert burger.available_quantity == 10
    assert pizza.available_quantity == 15
def test_payment_success_multiple_items(order_test_data):
    response = client.post("/orders/", json={
        "client_id": order_test_data["client_id"],
        "items": [
            {
                "item_id": order_test_data["item_id"],
                "quantity": 2
            },
            {
                "item_id": order_test_data["item2_id"],
                "quantity": 3
            }
        ]
    })

    assert response.status_code == 200
    order_id = response.json()["order_id"]

    payment_response = client.post(
        f"/orders/{order_id}/payment",
        json={"payment_success": True}
    )

    assert payment_response.status_code == 200
    assert payment_response.json()["payment_status"] == "SUCCESS"
    assert payment_response.json()["order_status"] == "CONFIRMED"

    db = order_test_data["db"]
    db.expire_all()

    burger = db.query(models.Item).filter(
        models.Item.item_id == order_test_data["item_id"]
    ).first()

    pizza = db.query(models.Item).filter(
        models.Item.item_id == order_test_data["item2_id"]
    ).first()

    # Stock remains deducted after successful payment
    assert burger.available_quantity == 8
    assert pizza.available_quantity == 12
def test_concurrent_orders_with_limited_stock(order_test_data):
    db = order_test_data["db"]
    item_id = order_test_data["item_id"]
    client_id = order_test_data["client_id"]

    item = db.query(models.Item).filter(
        models.Item.item_id == item_id
    ).first()

    item.available_quantity = 5
    db.commit()

    barrier = Barrier(2)

    def place_order(test_client):
        barrier.wait()

        return test_client.post("/orders/", json={
            "client_id": client_id,
            "items": [
                {"item_id": item_id, "quantity": 3}
            ]
        })

    with TestClient(client.app) as test_client:
        with ThreadPoolExecutor(max_workers=2) as executor:
            future1 = executor.submit(place_order, test_client)
            future2 = executor.submit(place_order, test_client)

            response1 = future1.result()
            response2 = future2.result()

    statuses = sorted([
        response1.status_code,
        response2.status_code
    ])

    assert statuses == [200, 400]

    db.expire_all()

    item = db.query(models.Item).filter(
        models.Item.item_id == item_id
    ).first()

    assert item.available_quantity == 2

    