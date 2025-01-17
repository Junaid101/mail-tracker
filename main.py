from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, ValidationError
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime
import os
from dotenv import load_dotenv
from enum import Enum
from contextlib import asynccontextmanager

# Load environment variables
if os.getenv("ENVIRONMENT") == "production":
    load_dotenv(".env.production")
else:
    load_dotenv(".env")

# MongoDB connection details
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
MONGODB_DB = os.getenv("MONGODB_DB", "email_tracker_db")
MONGODB_COLLECTION = os.getenv("MONGODB_COLLECTION", "emails")

# Define valid tenants
class TenantEnum(str, Enum):
    AADVANTO = "aadvanto"
    MOVIDO = "movido"

# Pydantic model for email tracking data
class EmailTrack(BaseModel):
    customer_number: str
    tenant: TenantEnum | None = None
    opened: bool = False
    timestamp: datetime | None = None
    count: int | None = 0

    class Config:
        extra = "ignore"

    def __init__(self, **data):
        if "timestamp" not in data:
            data["timestamp"] = datetime.utcnow()
        super().__init__(**data)

# Global variables for MongoDB client and collection
client = None
db = None
collection = None

# FastAPI app with lifespan context
@asynccontextmanager
async def lifespan(app):
    global client, db, collection
    # Initialize MongoDB client
    client = AsyncIOMotorClient(MONGODB_URI)
    db = client[MONGODB_DB]
    collection = db[MONGODB_COLLECTION]
    yield
    # Close MongoDB client on shutdown
    client.close()

app = FastAPI(lifespan=lifespan)

@app.get("/track-email/")
async def track_email(customer_number: str | None = None, tenant: str | None = None):
    try:
        if collection is None:
            raise HTTPException(status_code=500, detail="Database collection not initialized")

        email_data = EmailTrack(
            customer_number=customer_number,
            tenant=tenant
        )
        existing_record = await collection.find_one({"customer_number": customer_number, "tenant": tenant})
        if existing_record:
            result = await collection.update_one(
                {"_id": existing_record["_id"]},
                {
                    "$inc": {"count": 1},
                    "$set": {
                        "timestamp": datetime.utcnow(),
                        "tenant": tenant
                    }
                }
            )
            if result.modified_count:
                return {"message": "Email tracking data updated successfully!"}
        else:
            email_data = EmailTrack(
                customer_number=customer_number,
                tenant=tenant,
                count=1
            ).model_dump()
            result = await collection.insert_one(email_data)
            if result.inserted_id:
                return {"message": "Email tracking data saved successfully!"}

        raise HTTPException(status_code=500, detail="Failed to save email tracking data")
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "message": "Unknown Error",
                "errors": str(e)
            }
        )

@app.get("/")
def read_root():
    return {"message": "Welcome to the Email Tracker API v2.4.5!"}
