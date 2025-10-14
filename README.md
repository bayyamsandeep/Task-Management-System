# Task Management System Project (with Kafka consumer + events UI)

**Stack:** React (frontend) + FastAPI (backend) + MongoDB + Kafka + MinIO + Kafka Consumer API

This repository contains a sample full-stack project meant for learning cloud deployments (Azure App Service, ACI, AKS) and CI/CD (Azure DevOps). It runs locally with Docker Compose.

---

## What's included

- `backend/` - FastAPI app with CRUD endpoints for tasks, Kafka producer on create/update/delete, MinIO file upload support.
- `frontend/` - React app (list/create/delete tasks, upload files, and display Kafka events).
- `consumer/` - Kafka consumer service (FastAPI) which consumes messages from Kafka, stores events in MongoDB, and exposes `/events` endpoint.
- `docker-compose.yml` - Orchestrates MongoDB, Zookeeper, Kafka, MinIO, backend, consumer, and frontend.
- `k8s/` - Basic Kubernetes manifests.
- `azure-pipelines.yml` - Example Azure DevOps pipeline (build & push images, deploy to AKS).
- `.env` files and examples are included in service folders.

---

## Local setup (prerequisites)

- Docker & Docker Compose installed
- Ports 3000, 5000, 8000, 9000, 9092, 27017 available on your machine

---

## Run locally (Docker Compose)

1. Clone or unzip this project.
2. From the project root, run:
```bash
docker-compose up --build
```

This will start these services:
- Frontend: http://localhost:3000
- Backend (FastAPI): http://localhost:8000/docs
- Consumer API (events): http://localhost:5000/events
- MinIO console: http://localhost:9001 (username: minioadmin / password: minioadmin)

---

## Test the flow

1. Open frontend at `http://localhost:3000`
2. Create a new task — this will:
   - Store task in MongoDB (`tasks` collection)
   - Produce a Kafka message to topic `tasks`
3. Consumer (background) will consume the message, store an event in `events` collection, and the frontend polls `/events` to display it.
4. Upload a file from the frontend to test MinIO (check MinIO console at `http://localhost:9001`).
5. Inspect MongoDB with any client (e.g., MongoDB Compass) at `mongodb://localhost:27017`

---

## Useful commands

- View consumer logs:
```bash
docker logs -f consumer
```

- Rebuild a single service (e.g., backend):
```bash
docker-compose build backend
docker-compose up -d backend
```

- Stop and remove containers:
```bash
docker-compose down
```

---

## Next steps (Azure migration)

When you're ready, we can:
- Convert MongoDB to Cosmos DB (Mongo API)
- Replace Kafka with Azure Event Hubs (Kafka protocol)
- Replace MinIO with Azure Blob Storage
- Deploy backend/frontend to App Service / ACI / AKS
- Create Azure DevOps pipelines for CI/CD

---

Enjoy! If anything fails during `docker-compose up`, copy the logs here and I'll help debug.


## Real-time WebSocket & Admin UI


- The consumer service now exposes a WebSocket at `ws://localhost:5000/ws`. The Admin UI connects to it and shows live Kafka events.
- The frontend has an **Admin** tab where you can view live events and all tasks (Admin -> Live Events).
- Polling is still available on the Home page as a fallback.

### Testing WebSocket
1. Start services: `docker-compose up --build`
2. Open frontend: http://localhost:3000
3. Click **Admin** tab — you should see live events appear when tasks are created or updated.
4. You can also `curl` or open `http://localhost:5000/events` to fetch recent events.

