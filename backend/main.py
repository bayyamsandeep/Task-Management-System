import os
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pymongo import MongoClient, errors
from bson.objectid import ObjectId

MONGO_URI = os.getenv("MONGO_URI", "localhost:27017")
DB_NAME = "tasksdb"
COLLECTION_NAME = "tasks"

app = FastAPI(title="Task Management API")

client = None
db = None
tasks_col = None

# Allow CORS from frontend (adjust origin as needed)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup_db_client():
    global client, db, tasks_col
    try:
        if not MONGO_URI:
            raise RuntimeError("❌ MONGO_URI environment variable not set.")

        client = MongoClient(MONGO_URI)
        db = client[DB_NAME]

        # Ensure collection exists
        if COLLECTION_NAME not in db.list_collection_names():
            db.create_collection(COLLECTION_NAME)
            print(f"🆕 Created collection '{COLLECTION_NAME}' in database '{DB_NAME}'")

        tasks_col = db[COLLECTION_NAME]
        print("✅ MongoDB connection established and verified.")

    except errors.ConnectionFailure as e:
        print("❌ MongoDB connection failed:", e)
        raise e


@app.on_event("shutdown")
def shutdown_db_client():
    if client:
        client.close()
        print("🔒 MongoDB connection closed.")


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
    task_data.pop("_id", None)
    result = tasks_col.update_one({"_id": ObjectId(task_id)}, {"$set": task_data})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Task not found")

    updated_task = tasks_col.find_one({"_id": ObjectId(task_id)})
    return serialize_task(updated_task)


@app.delete("/tasks/{task_id}")
def delete_task(task_id: str):
    task = tasks_col.find_one({"_id": ObjectId(task_id)})
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    tasks_col.delete_one({"_id": ObjectId(task_id)})
    return {"status": "deleted", "id": task_id}


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
