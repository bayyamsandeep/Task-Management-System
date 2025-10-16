from fastapi import FastAPI, HTTPException, UploadFile, File, Request
from fastapi.middleware.cors import CORSMiddleware
from typing import List
from pymongo import MongoClient
from bson.objectid import ObjectId
import os
import json
# from kafka import KafkaProducer
import boto3
from botocore.client import Config
# from dotenv import load_dotenv

# load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "")
KAFKA_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP", "")
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "")
MINIO_BUCKET = os.getenv("MINIO_BUCKET", "uploads")

if not MONGO_URI:
    raise RuntimeError("❌ MONGO_URI environment variable not set.")

try:
    client = MongoClient(MONGO_URI)
    db = client.get_database("tasksdb")  # or any DB name you use
    print("✅ Connected to MongoDB (CosmosDB) successfully.")
except Exception as e:
    print("❌ MongoDB connection failed:", e)
    raise e

# Kafka producer (simple)
# producer = KafkaProducer(
#     bootstrap_servers=[KAFKA_BOOTSTRAP],
#     value_serializer=lambda v: json.dumps(v).encode("utf-8"),
#     retries=5
# )

# # MinIO (S3 compatible) client via boto3
# s3 = boto3.client(
#     "s3",
#     endpoint_url=f"http://{MINIO_ENDPOINT}",
#     aws_access_key_id=MINIO_ACCESS_KEY,
#     aws_secret_access_key=MINIO_SECRET_KEY,
#     config=Config(signature_version="s3v4"),
#     region_name="us-east-1"
# )

# # ensure bucket exists (for local, may fail in some cloud envs)
# try:
#     s3.create_bucket(Bucket=MINIO_BUCKET)
# except Exception:
#     pass

app = FastAPI(title="Task Management API")

# Allow CORS from frontend (adjust origin as needed)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {"message": "Task Management API is running"}


@app.get("/health")
def health():
    return {"status": "ok"}


def serialize_task(task):
    """Convert MongoDB object to JSON serializable dict"""
    task["_id"] = str(task["_id"])
    return task


@app.post("/tasks")
async def create_task(request: Request):
    task_data = await request.json()
    if "title" not in task_data:
        raise HTTPException(status_code=400, detail="Missing 'title'")
    task_data.setdefault("description", "")
    task_data.setdefault("done", False)

    res = tasks_col.insert_one(task_data)
    task_data["_id"] = str(res.inserted_id)

    # send kafka event
    # try:
    #     producer.send("tasks", {"action": "create", "task": task_data})
    #     producer.flush()
    # except Exception as e:
    #     print("Kafka produce error", e)

    return task_data


@app.get("/tasks")
def list_tasks():
    tasks = list(tasks_col.find())
    return [serialize_task(t) for t in tasks]


@app.get("/tasks/{task_id}")
def get_task(task_id: str):
    task = tasks_col.find_one({"_id": ObjectId(task_id)})
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return serialize_task(task)


@app.put("/tasks/{task_id}")
async def update_task(task_id: str, request: Request):
    task_data = await request.json()
    result = tasks_col.update_one({"_id": ObjectId(task_id)}, {"$set": task_data})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Task not found")

    updated_task = tasks_col.find_one({"_id": ObjectId(task_id)})

    # try:
    #     producer.send("tasks", {"action": "update", "task": updated_task})
    #     producer.flush()
    # except Exception as e:
    #     print("Kafka produce error", e)

    return serialize_task(updated_task)


@app.delete("/tasks/{task_id}")
def delete_task(task_id: str):
    task = tasks_col.find_one({"_id": ObjectId(task_id)})
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    tasks_col.delete_one({"_id": ObjectId(task_id)})

    # try:
    #     producer.send("tasks", {"action": "delete", "task_id": task_id})
    #     producer.flush()
    # except Exception as e:
    #     print("Kafka produce error", e)

    return {"status": "deleted", "id": task_id}


@app.post("/upload")
def upload_file(file: UploadFile = File(...)):
    # data = file.file.read()
    # key = file.filename
    # s3.put_object(Bucket=MINIO_BUCKET, Key=key, Body=data)
    # url = f"http://{MINIO_ENDPOINT}/{MINIO_BUCKET}/{key}"
    # return {"filename": key, "url": url}
    return {"filename": file.filename, "status": "Success"}


if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
