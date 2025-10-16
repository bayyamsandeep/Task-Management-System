# Task Management System Project

**Stack:** React (frontend) + FastAPI (backend) + MongoDB 

This repository contains a sample full-stack project meant for learning cloud deployments (Azure App Service, ACI, AKS) and CI/CD (Azure DevOps). It runs locally with Docker Compose.

---

## What's included

- `backend/` - FastAPI app with CRUD endpoints for tasks create/update/delete.
- `frontend/` - React app (list/create/delete tasks).


---

## Local setup (prerequisites)

- Docker & Docker Compose installed
- Ports 3000, 8000, 9000, 9092, 27017 available on your machine
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
---

## Test the flow
1. Start services: `docker-compose up --build`
2. Open frontend at `http://localhost:3000`
3. Create a new task — this will:
   - Store task in MongoDB (`tasks` collection)
4. Inspect MongoDB with any client (e.g., MongoDB Compass) at `mongodb://localhost:27017`

---

## Next steps (Azure migration)

When you're ready, we can:
- Convert MongoDB to Cosmos DB (Mongo API)
- Deploy backend/frontend to App Service / ACI / AKS
- Create Azure DevOps pipelines for CI/CD

---

Enjoy! If anything fails during `docker-compose up`, copy the logs here and I'll help debug.
