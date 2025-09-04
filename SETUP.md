# Sportify Setup Guide 🚀

This guide will help you get Sportify running locally on your machine.

## Prerequisites

Before you begin, make sure you have the following installed:

- **Docker & Docker Compose** - [Install Docker](https://docs.docker.com/get-docker/)
- **Python 3.9+** - [Install Python](https://www.python.org/downloads/)
- **Node.js 18+** - [Install Node.js](https://nodejs.org/)
- **Git** - [Install Git](https://git-scm.com/)

## Quick Start (Recommended)

The fastest way to get Sportify running is using Docker Compose:

### 1. Clone and Setup

```bash
# Clone the repository
git clone <your-repo-url>
cd Sportify

# Start all services
docker-compose up -d
```

This will start:

- PostgreSQL database on port 5432
- FastAPI backend on port 8000
- Next.js frontend on port 3000

### 2. Access the Application

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

### 3. Seed Demo Data

```bash
# Seed the database with demo data
curl -X POST http://localhost:8000/seed/demo
```

### 4. Test the Backend

```bash
# Run the test script
python test_backend.py
```

## Manual Setup (Development)

If you prefer to run services individually for development:

### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export DATABASE_URL="postgresql://sportify_user:sportify_password@localhost:5432/sportify"

# Start the backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start the development server
npm run dev
```

### Database Setup

```bash
# Start PostgreSQL (if not using Docker)
docker run -d \
  --name sportify_postgres \
  -e POSTGRES_DB=sportify \
  -e POSTGRES_USER=sportify_user \
  -e POSTGRES_PASSWORD=sportify_password \
  -p 5432:5432 \
  postgres:15-alpine

# Wait for database to be ready, then initialize
psql -h localhost -U sportify_user -d sportify -f backend/init.sql
```

## Project Structure

```
Sportify/
├── backend/                 # FastAPI backend
│   ├── app/
│   │   ├── models.py       # SQLAlchemy models
│   │   ├── schemas.py      # Pydantic schemas
│   │   ├── database.py     # Database configuration
│   │   └── scheduler.py    # OR-Tools scheduler
│   ├── main.py             # FastAPI application
│   ├── requirements.txt    # Python dependencies
│   ├── Dockerfile          # Backend container
│   └── init.sql           # Database initialization
├── frontend/               # Next.js frontend
│   ├── app/               # Next.js app directory
│   ├── package.json       # Node.js dependencies
│   ├── tailwind.config.js # TailwindCSS configuration
│   └── Dockerfile         # Frontend container
├── docker-compose.yml      # Service orchestration
├── test_backend.py         # Backend testing script
├── README.md              # Project overview
└── SETUP.md               # This file
```

## API Endpoints

### Core Endpoints

- `GET /health` - Health check
- `POST /seed/demo` - Seed demo data
- `POST /scheduler/run` - Run tournament scheduler

### Tournament Management

- `GET /tournaments` - List tournaments
- `POST /tournaments` - Create tournament
- `GET /tournaments/{id}` - Get tournament
- `PUT /tournaments/{id}` - Update tournament
- `DELETE /tournaments/{id}` - Delete tournament

### Team Management

- `GET /teams` - List teams
- `POST /teams` - Create team
- `GET /teams/{id}` - Get team
- `PUT /teams/{id}` - Update team

### Scheduling

- `GET /matches` - List matches
- `GET /schedules` - List schedules
- `POST /export/{format}` - Export schedules

## Testing

### Backend Testing

```bash
# Run the test script
python test_backend.py

# Test individual endpoints
curl http://localhost:8000/health
curl http://localhost:8000/tournaments
curl -X POST http://localhost:8000/seed/demo
```

### Frontend Testing

```bash
cd frontend
npm run build
npm start
```

## Troubleshooting

### Common Issues

1. **Port already in use**

   ```bash
   # Find and kill process using port 8000
   lsof -ti:8000 | xargs kill -9
   ```

2. **Database connection failed**

   ```bash
   # Check if PostgreSQL is running
   docker ps | grep postgres

   # Restart database
   docker-compose restart postgres
   ```

3. **Dependencies not found**

   ```bash
   # Rebuild containers
   docker-compose down
   docker-compose build --no-cache
   docker-compose up -d
   ```

4. **Frontend build errors**
   ```bash
   cd frontend
   rm -rf node_modules package-lock.json
   npm install
   ```

### Logs

```bash
# View all service logs
docker-compose logs

# View specific service logs
docker-compose logs backend
docker-compose logs frontend
docker-compose logs postgres

# Follow logs in real-time
docker-compose logs -f
```

## Development Workflow

1. **Make changes** to backend or frontend code
2. **Restart services** if needed:
   ```bash
   docker-compose restart backend  # For backend changes
   docker-compose restart frontend # For frontend changes
   ```
3. **Test changes** using the test script or manual API calls
4. **Commit and push** your changes

## Next Steps

After getting Sportify running locally:

1. **Explore the API** at http://localhost:8000/docs
2. **Test the scheduler** by creating tournaments and running schedules
3. **Customize the frontend** by modifying components in `frontend/app/`
4. **Add new features** to the backend in `backend/app/`
5. **Extend the scheduler** with new constraints in `backend/app/scheduler.py`

## Support

If you encounter issues:

1. Check the logs: `docker-compose logs`
2. Verify all services are running: `docker-compose ps`
3. Check the troubleshooting section above
4. Review the API documentation: http://localhost:8000/docs

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

---

**Happy Scheduling! 🏀⚽🎾**
