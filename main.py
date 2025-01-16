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
    email_id: str | None = None
    opened: bool = False
    timestamp: datetime | None = None

    class Config:
        extra = "ignore"  # Ignore additional fields in the input
        
    def __init__(self, **data):
        if "timestamp" not in data:
            data["timestamp"] = datetime.utcnow()
        super().__init__(**data)

@app.get("/track-email/")
async def track_email(customer_number: str | None = None, email_id: str | None = None):
    email_data = EmailTrack(customer_number=customer_number, email_id=email_id).dict()

    print(email_data)
    # Insert the email tracking data into the MongoDB collection
    result = await collection.insert_one(email_data)
    if result.inserted_id:
        return {"message": "Email tracking data saved successfully!"}
    else:
        raise HTTPException(status_code=500, detail="Failed to save email tracking data")

@app.get("/")
def read_root():
    return {"message": "Welcome to the Email Tracker API 2!"}

