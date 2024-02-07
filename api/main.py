from fastapi import FastAPI

app = FastAPI()


# source .venv/Scripts/activate


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
