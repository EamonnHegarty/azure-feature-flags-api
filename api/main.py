import json
import os

from azure.appconfiguration import AzureAppConfigurationClient
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

# app configuration connection
app_configuration_connection_string = os.getenv("APP_CONFIGURATION_CONNECTION_STRING")


class FeatureFlagsRequest(BaseModel):
    tenant: str


@app.get("/")
async def root():
    return {"message": "hello world"}


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


@app.get("/config-app-config")
async def get_all_app_config_settings():

    client = AzureAppConfigurationClient.from_connection_string(
        app_configuration_connection_string
    )

    try:

        feature_flags = client.list_configuration_settings(
            key_filter=".appconfig.featureflag/*"
        )

        feature_flags_list = []
        for feature_flag in feature_flags:
            parsed_value = json.loads(feature_flag.value)
            flag = {
                "key": feature_flag.key,
                "value": parsed_value,
                "label": feature_flag.label,
            }
            feature_flags_list.append(flag)

        configs = client.list_configuration_settings(key_filter="*")

        configs_list = []
        for config in configs:
            if not config.key.startswith(".appconfig.featureflag/"):
                parsed_value = (
                    json.loads(config.value)
                    if config.value.startswith("[")
                    else config.value
                )
                conf = {
                    "key": config.key,
                    "value": parsed_value,
                    "label": config.label,
                }
                configs_list.append(conf)

    except Exception as e:
        return {"error": str(e)}

    return {"featureFlags": feature_flags_list, "configurations": configs_list}
