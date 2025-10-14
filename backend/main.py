
from fastapi import FastAPI, HTTPException, UploadFile, File, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List
from pymongo import MongoClient
from bson.objectid import ObjectId
import os
import json
import io
from kafka import KafkaProducer
import boto3
from botocore.client import Config
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/tasksdb")
KAFKA_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP", "localhost:9092")
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "localhost:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "minioadmin")
MINIO_BUCKET = os.getenv("MINIO_BUCKET", "uploads")

client = MongoClient(MONGO_URI)
db = client.get_default_database() if client else client['tasksdb']
tasks_col = db.get_collection("tasks")

# Kafka producer (simple)
producer = KafkaProducer(bootstrap_servers=[KAFKA_BOOTSTRAP],
                         value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                         retries=5)

# MinIO (S3 compatible) client via boto3
s3 = boto3.client('s3',
                  endpoint_url=f'http://{MINIO_ENDPOINT}',
                  aws_access_key_id=MINIO_ACCESS_KEY,
                  aws_secret_access_key=MINIO_SECRET_KEY,
                  config=Config(signature_version='s3v4'),
                  region_name='us-east-1')

# ensure bucket exists (for local, may fail in some cloud envs)
try:
    s3.create_bucket(Bucket=MINIO_BUCKET)
except Exception:
    pass

app = FastAPI(title='Task Management API')

# Allow CORS from frontend (adjust origin as needed)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get('/')
def root():
    return {'message': 'Task Management API is running'}


@app.get('/health')
def health():
    return {'status': 'ok'}


class Task(BaseModel):
    title: str = Field(..., example='Buy apples')
    description: str = Field('', example='Details')
    done: bool = False


def task_to_dict(t):
    t['_id'] = str(t['_id'])
    return t


@app.post('/tasks', response_model=dict)
def create_task(task: Task):
    doc = task.dict()
    res = tasks_col.insert_one(doc)
    doc['_id'] = str(res.inserted_id)
    # send kafka event
    try:
        producer.send('tasks', {'action': 'create', 'task': doc})
        producer.flush()
    except Exception as e:
        print('Kafka produce error', e)
    return doc


@app.get('/tasks', response_model=List[dict])
def list_tasks():
    items = list(tasks_col.find())
    for i in items:
        i['_id'] = str(i['_id'])
    return items


@app.get('/tasks/{task_id}', response_model=dict)
def get_task(task_id: str):
    item = tasks_col.find_one({'_id': ObjectId(task_id)})
    if not item:
        raise HTTPException(status_code=404, detail='Not found')
    item['_id'] = str(item['_id'])
    return item


@app.put('/tasks/{task_id}', response_model=dict)
def update_task(task_id: str, task: Task):
    res = tasks_col.update_one({'_id': ObjectId(task_id)}, {'$set': task.dict()})
    if res.matched_count == 0:
        raise HTTPException(status_code=404, detail='Not found')
    item = tasks_col.find_one({'_id': ObjectId(task_id)})
    item['_id'] = str(item['_id'])
    try:
        producer.send('tasks', {'action': 'update', 'task': item})
        producer.flush()
    except Exception as e:
        print('Kafka produce error', e)
    return item


@app.delete('/tasks/{task_id}', response_model=dict)
def delete_task(task_id: str):
    item = tasks_col.find_one({'_id': ObjectId(task_id)})
    if not item:
        raise HTTPException(status_code=404, detail='Not found')
    tasks_col.delete_one({'_id': ObjectId(task_id)})
    try:
        producer.send('tasks', {'action': 'delete', 'task_id': task_id})
        producer.flush()
    except Exception as e:
        print('Kafka produce error', e)
    return {'status': 'deleted', 'id': task_id}


@app.post('/upload', response_model=dict)
def upload_file(file: UploadFile = File(...)):
    data = file.file.read()
    key = file.filename
    s3.put_object(Bucket=MINIO_BUCKET, Key=key, Body=data)
    url = f'http://{MINIO_ENDPOINT}/{MINIO_BUCKET}/{key}'
    return {'filename': key, 'url': url}
