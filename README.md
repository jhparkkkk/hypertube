# Hypertube - Streaming Platform

## Description
Hypertube is a video search and streaming platform using **React (frontend), Django (backend), PostgreSQL (database), and Nginx (reverse proxy)**, orchestrated with **Docker**.

## Setup
### 1. Clone the Repository
```bash
git clone <REPO_URL>
cd hypertube
```

### 2. Run the Project

```bash
docker-compose up --build
```

## Access the Application
- **Frontend**: [http://localhost/](http://localhost/)
- **Backend API**: [http://localhost/api/](http://localhost/api/)


## Project Structure
```
├── backend/       # Django API
├── frontend/      # React UI
├── nginx/         # Reverse proxy config
├── docker-compose.yml
├── README.md
```

