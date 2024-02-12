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


@app.post("/config-cosmos")
async def get_feature_flags(request: FeatureFlagsRequest):
    tenant = request.tenant

    feature_flag_query = (
        f"SELECT c.id, f.flags FROM c JOIN f IN c.tenant WHERE f.tenant = '{tenant}'"
    )
    feature_flags = list(
        container.query_items(
            query=feature_flag_query, enable_cross_partition_query=True
        )
    )

    config_container_name = "config"
    config_container = database.get_container_client(config_container_name)

    config_query = f"SELECT c.configuration FROM c WHERE c.tenant = '{tenant}'"
    config_items = list(
        config_container.query_items(
            query=config_query, enable_cross_partition_query=True
        )
    )

    result = {}

    if feature_flags:
        result["flags"] = feature_flags[0].get("flags", {})
    if config_items:
        result["configuration"] = config_items[0].get("configuration", [])

    return result
