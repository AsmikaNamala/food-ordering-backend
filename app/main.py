
from contextlib import asynccontextmanager
from fastapi import FastAPI

from app.routers import vendors, clients, items, orders, replenishment
from app.scheduler import start_scheduler, stop_scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Start scheduler when application starts
    start_scheduler()

    yield

    # Stop scheduler when application shuts down
    stop_scheduler()


app = FastAPI(
    title="Food Ordering Backend",
    description="Food Ordering and Inventory Management System",
    version="1.0.0",
    lifespan=lifespan
)


app.include_router(vendors.router)
app.include_router(clients.router)
app.include_router(items.router)
app.include_router(orders.router)
app.include_router(replenishment.router)


@app.get("/")
def home():
    return {"message": "Welcome to Food Ordering Backend"}


@app.get("/health")
def health():
    return {"status": "healthy"}
