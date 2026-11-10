
import os
import pytest

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.engine import make_url

from app.database import Base
from app import models
from app.dependencies import get_db
from app.main import app


# Load the existing database configuration
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is missing from .env")

# Build a separate test database URL
original_url = make_url(DATABASE_URL)

if original_url.database != "food_ordering":
    raise RuntimeError(
        "Expected the original database to be food_ordering"
    )

TEST_DATABASE_URL = original_url.set(
    database="food_ordering_test"
)

# Connect to the test database
test_engine = create_engine(
    TEST_DATABASE_URL,
    pool_pre_ping=True
)

TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=test_engine
)


# Provide test database sessions to FastAPI
def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


# Set up the test database before running tests
@pytest.fixture(scope="session", autouse=True)
def setup_test_database():

    if test_engine.url.database != "food_ordering_test":
        raise RuntimeError("Unsafe test database configuration")

    Base.metadata.create_all(bind=test_engine)

    app.dependency_overrides[get_db] = override_get_db

    yield

    app.dependency_overrides.clear()
    test_engine.dispose()

from uuid import uuid4

@pytest.fixture
def order_test_data():
    db = TestingSessionLocal()

    unique_id = str(uuid4())

    test_client = models.Client(
        client_name="Test Client",
        email=f"test_{unique_id}@example.com"
    )

    test_item = models.Item(
        item_name=f"Test Burger {unique_id}",
        available_quantity=10,
        minimum_quantity=2,
        price=100
    )

    test_item2 = models.Item(
        item_name=f"Test Pizza {unique_id}",
        available_quantity=15,
        minimum_quantity=3,
        price=200
    )

    db.add_all([test_client, test_item, test_item2])
    db.commit()

    db.refresh(test_client)
    db.refresh(test_item)
    db.refresh(test_item2)

    data = {
        "client_id": test_client.client_id,
        "item_id": test_item.item_id,
        "item2_id": test_item2.item_id,
        "db": db
    }

    try:
        yield data

    finally:
        orders = db.query(models.Order).filter(
            models.Order.client_id == test_client.client_id
        ).all()

        order_ids = [order.order_id for order in orders]

        if order_ids:
            db.query(models.OrderItem).filter(
                models.OrderItem.order_id.in_(order_ids)
            ).delete(synchronize_session=False)

            db.query(models.Order).filter(
                models.Order.order_id.in_(order_ids)
            ).delete(synchronize_session=False)

        db.delete(test_item)
        db.delete(test_item2)
        db.delete(test_client)

        db.commit()
        db.close()