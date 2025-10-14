
import os
import json
import time
import threading
import asyncio
from typing import List
from kafka import KafkaConsumer
from pymongo import MongoClient
from dotenv import load_dotenv
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

KAFKA_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP", "kafka:9092")
MONGO_URI = os.getenv("MONGO_URI", "mongodb://mongo:27017/tasksdb")
TOPIC = os.getenv("KAFKA_TOPIC", "tasks")
CONSUMER_GROUP = os.getenv("KAFKA_CONSUMER_GROUP", "task-consumers")

app = FastAPI(title="Task Management Kafka Consumer API with WebSocket")

# Allow CORS from frontend (adjust origin as needed)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

mongo = MongoClient(MONGO_URI)
db = mongo.get_default_database() if mongo else mongo['tasksdb']
events_col = db.get_collection("events")


# WebSocket manager
class ConnectionManager:
    def __init__(self):
        self.active: List[WebSocket] = []
        self.lock = threading.Lock()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        with self.lock:
            self.active.append(websocket)

    def disconnect(self, websocket: WebSocket):
        with self.lock:
            if websocket in self.active:
                self.active.remove(websocket)

    async def broadcast(self, message: dict):
        # send concurrently to all websockets
        to_remove = []
        coros = []
        for ws in list(self.active):
            coros.append(self._send_safe(ws, message))
        if coros:
            await asyncio.gather(*coros, return_exceptions=True)

    async def _send_safe(self, ws: WebSocket, message: dict):
        try:
            await ws.send_json(message)
        except Exception:
            # mark for removal
            try:
                self.disconnect(ws)
            except Exception:
                pass


manager = ConnectionManager()

# In-memory cap for recent events (optional)
RECENT_EVENTS_LIMIT = 500


def store_event(evt):
    try:
        events_col.insert_one(evt)
    except Exception as e:
        print("Failed to store event:", e)


def consume_loop(loop):
    print("Starting Kafka consumer loop in background thread...")
    try:
        consumer = KafkaConsumer(
            TOPIC,
            bootstrap_servers=[KAFKA_BOOTSTRAP],
            value_deserializer=lambda m: json.loads(m.decode('utf-8')),
            auto_offset_reset='earliest',
            enable_auto_commit=True,
            group_id=CONSUMER_GROUP
        )
        for msg in consumer:
            print(f"Consumed message: {msg.value}")
            evt = {
                "topic": msg.topic,
                "partition": msg.partition,
                "offset": msg.offset,
                "value": msg.value,
                "timestamp": int(time.time())
            }
            # persist
            store_event(evt)
            # broadcast to websockets via asyncio loop
            try:
                asyncio.run_coroutine_threadsafe(manager.broadcast(evt), loop)
            except Exception as e:
                print("Failed to schedule broadcast:", e)
    except Exception as e:
        print("Consumer encountered error:", e)


@app.get("/")
def root():
    return {"message": "Task Manegement Consumer API is running"}


@app.get("/health")
def health():
    return {"status": "ok"}


# Start consumer in background thread when app starts
@app.on_event("startup")
def startup_event():
    loop = asyncio.get_event_loop()
    t = threading.Thread(target=consume_loop, args=(loop,), daemon=True)
    t.start()


class EventOut(BaseModel):
    topic: str
    partition: int
    offset: int
    value: dict
    timestamp: int


@app.get("/events", response_model=List[EventOut])
def get_events(limit: int = 50):
    items = list(events_col.find().sort("timestamp", -1).limit(limit))
    out = []
    for it in items:
        it.pop('_id', None)
        out.append(it)
    return out


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # keep connection open; client may send ping messages
            _ = await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception:
        manager.disconnect(websocket)
