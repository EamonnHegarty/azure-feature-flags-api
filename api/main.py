import os

from azure.cosmos import CosmosClient, exceptions
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

load_dotenv()

# uvicorn api.main:app --reload --port 8080

app = FastAPI()

# Add CORSMiddleware to the application instance
origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Cosmos DB credentials
url = os.getenv("COSMOS_DB_URL")
key = os.getenv("COSMOS_DB_KEY")
client = CosmosClient(url, credential=key)

# Reference to db and container
database_name = "FeatureFlags"
container_name = "flags"
database = client.get_database_client(database_name)
container = database.get_container_client(container_name)

# this would be got from the azure secret for tenant so be tenant ID that way we can return the results for a tenant
# so EU would have one set of configs/flags and so on


class FeatureFlagsRequest(BaseModel):
    tenant: str


@app.get("/")
async def root():
    return {"message": "hello world"}


@app.get("/data")
async def get_data():
    return [
        {"_id": 1, "data": "data 1"},
        {"_id": 2, "data": "data 2"},
        {"_id": 3, "data": "data 3"},
    ]


@app.post("/feature-flags")
async def get_feature_flags(request: FeatureFlagsRequest):
    tenant = request.tenant

    query = (
        f"SELECT c.id, f.flags FROM c JOIN f IN c.tenant WHERE f.tenant = '{tenant}'"
    )
    items = list(container.query_items(query=query, enable_cross_partition_query=True))
    return items


@app.get("/modules")
async def get_modules():
    return ["modules"]
