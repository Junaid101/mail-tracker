from sanic import Sanic, json
from sanic.exceptions import SanicException
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime
import os
from dotenv import load_dotenv
from enum import Enum
from pydantic import BaseModel, ValidationError

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

# Initialize Sanic app
app = Sanic("email_tracker")

# Database connection function
async def get_database():
    try:
        client = AsyncIOMotorClient(MONGODB_URI)
        await client.admin.command('ping')
        return client[MONGODB_DB][MONGODB_COLLECTION]
    except Exception as e:
        return None

# Define validation model
class EmailTrackRequest(BaseModel):
    customer_number: str
    tenant: TenantEnum

@app.get("/track-email")
async def track_email(request):
    try:
        # Validate request data
        try:
            data = EmailTrackRequest(
                customer_number=request.args.get('customer_number'),
                tenant=request.args.get('tenant')
            )
        except ValidationError as e:
            return json(
                {
                    "message": "Validation error",
                    "errors": e.errors()
                },
                status=400
            )

        collection = await get_database()
        if collection is None:
            return json(
                {
                    "message": "Database connection failed",
                    "errors": "Could not establish database connection"
                },
                status=500
            )

        # Try to find existing record
        existing_record = await collection.find_one({
            "customer_number": data.customer_number,
            "tenant": data.tenant
        })

        if existing_record:
            result = await collection.update_one(
                {"_id": existing_record["_id"]},
                {
                    "$inc": {"count": 1},
                    "$set": {
                        "timestamp": datetime.utcnow(),
                        "tenant": data.tenant
                    }
                }
            )
            if result.modified_count:
                return json({"message": "Email tracking data updated successfully!"})
        else:
            email_data = {
                "customer_number": data.customer_number,
                "tenant": data.tenant,
                "timestamp": datetime.utcnow(),
                "count": 1
            }
            result = await collection.insert_one(email_data)
            if result.inserted_id:
                return json({"message": "Email tracking data saved successfully!"})

        return json(
            {"message": "Failed to save email tracking data"},
            status=500
        )

    except Exception as e:
        return json(
            {
                "message": "Unknown Error",
                "errors": str(e)
            },
            status=500
        )

@app.get("/")
async def read_root(request):
    return json({"message": "Welcome to the Email Tracker API v2.4.5!"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
