from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables
if os.getenv("ENVIRONMENT") == "production":
    load_dotenv(".env.production")
else:
    load_dotenv(".env")

app = FastAPI()

# MongoDB connection details
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
MONGODB_DB = os.getenv("MONGODB_DB", "email_tracker_db")
MONGODB_COLLECTION = os.getenv("MONGODB_COLLECTION", "emails")

# Initialize the MongoDB client
client = AsyncIOMotorClient(MONGODB_URI)
db = client[MONGODB_DB]
collection = db[MONGODB_COLLECTION]

# Pydantic model for email tracking data
class EmailTrack(BaseModel):
    customer_number: str | None = None
    tenant: str | None = None
    opened: bool = False
    timestamp: datetime | None = None

    class Config:
        extra = "ignore"  # Ignore additional fields in the input
        
    def __init__(self, **data):
        if "timestamp" not in data:
            data["timestamp"] = datetime.utcnow()
        super().__init__(**data)

@app.get("/track-email/")
async def track_email(customer_number: str | None = None, tenant: str | None = None):
    if not customer_number:
        raise HTTPException(status_code=400, detail="customer_number is required")

    # Try to find existing record for this customer
    existing_record = await collection.find_one({"customer_number": customer_number})
    
    if existing_record:
        # Update existing record with incremented count and new timestamp
        result = await collection.update_one(
            {"customer_number": customer_number},
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
        # Create new record with initial count of 1
        email_data = EmailTrack(
            customer_number=customer_number,
            tenant=tenant,
            count=1
        ).dict()
        result = await collection.insert_one(email_data)
        if result.inserted_id:
            return {"message": "Email tracking data saved successfully!"}

    raise HTTPException(status_code=500, detail="Failed to save email tracking data")

@app.get("/")
def read_root():
    return {"message": "Welcome to the Email Tracker API 2!"}

