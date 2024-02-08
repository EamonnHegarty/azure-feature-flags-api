import os

from azure.cosmos import CosmosClient, exceptions
from dotenv import load_dotenv
from fastapi import FastAPI

# source .venv/Scripts/activate
# uvicorn api.main:app --reload

load_dotenv()


app = FastAPI()

# Cosmos DB credentials
url = os.getenv("COSMOS_DB_URL")
key = os.getenv("COSMOS_DB_KEY")
client = CosmosClient(url, credential=key)

# Reference to your database and container
database_name = "FeatureFlags"
container_name = "flags"
database = client.get_database_client(database_name)
container = database.get_container_client(container_name)

# this would be got from the azure secret for tenant so be tenant ID that way we can return the results for a tenant
# so EU would have one set of configs/flags and so on
tenant = "EU"


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


@app.get("/feature-flags")
async def get_feature_flags():

    query = (
        f"SELECT c.id, f.flags FROM c JOIN f IN c.tenant WHERE f.tenant = '{tenant}'"
    )
    items = list(container.query_items(query=query, enable_cross_partition_query=True))
    return items


@app.get("/modules")
async def get_modules():
    return ["modules"]
