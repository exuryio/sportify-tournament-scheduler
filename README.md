# Sportify 🏀

**Automated Sports Tournament Scheduling Platform**

Sportify is a SaaS platform that automates the creation of weekly match schedules for amateur sports tournaments using Google OR-Tools optimization algorithms.

## 🎯 Problem & Solution

**Problem**: Tournament organizers spend excessive time manually creating weekly match schedules while juggling multiple constraints:

- Limited court availability
- Team-specific time preferences
- Fairness considerations
- Conflict prevention

**Solution**: Sportify automates scheduling using constraint programming (CP-SAT) to generate optimal schedules that respect all constraints and optimize for fairness.

## 🏗️ Architecture

- **Backend**: FastAPI (Python) with SQLAlchemy + PostgreSQL
- **Optimization Engine**: Google OR-Tools (CP-SAT)
- **Frontend**: React/Next.js with TailwindCSS
- **Infrastructure**: Docker + docker-compose for local development

## 🚀 MVP Features (4 weeks)

- [x] Database schema (tournaments, teams, matches, courts, slots, schedules)
- [x] Demo data seeding (3 tournaments, 2 courts, 12 slots)
- [x] OR-Tools scheduler with CP-SAT
- [x] REST API endpoints
- [x] Schedule export (JSON/CSV)

## 🛠️ Getting Started

### Prerequisites

- Docker & Docker Compose
- Python 3.9+
- Node.js 18+

### Quick Start

```bash
# Clone and setup
git clone <repository>
cd Sportify

# Start all services
docker-compose up -d

# The application will be available at:
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
# Database: localhost:5432
```

### Development

```bash
# Backend development
cd backend
pip install -r requirements.txt
uvicorn main:app --reload

# Frontend development
cd frontend
npm install
npm run dev
```

## 📊 Database Schema

- **Tournaments**: Basic tournament info and settings
- **Teams**: Team details and availability windows
- **Courts**: Available playing surfaces
- **TimeSlots**: Available time periods
- **Matches**: Individual games with team assignments
- **Schedules**: Complete weekly schedules

## 🔧 API Endpoints

- `POST /scheduler/run` - Generate new schedule
- `GET /tournaments` - List all tournaments
- `GET /teams` - List teams with availability
- `GET /matches` - Get scheduled matches
- `GET /schedules` - Get complete schedules
- `POST /export/{format}` - Export schedules

## 🎨 Future Features

- Team captain portal for availability submission
- Drag & drop schedule editor
- Email/WhatsApp notifications
- Advanced fairness constraints
- Multi-sport support

## 📝 License

MIT License - see LICENSE file for details
