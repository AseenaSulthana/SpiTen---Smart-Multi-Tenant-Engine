# SpiTen Backend

FastAPI-based multi-tenant organization management engine with MongoDB.

## Features

- Async FastAPI framework
- MongoDB with motor driver
- JWT authentication with bcrypt password hashing
- Dynamic tenant collection creation
- Full CRUD operations for organizations
- Admin user management
- System metrics endpoint

## Setup

### Prerequisites

- Python 3.11+
- MongoDB (external instance required)
- pip

### Installation

1. **Create virtual environment:**
   \`\`\`bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   \`\`\`

2. **Install dependencies:**
   \`\`\`bash
   pip install -r requirements.txt
   \`\`\`

3. **Configure environment variables:**
   \`\`\`bash
   cp .env.example .env
   \`\`\`
   
   Edit `.env` and set:
   - `MONGODB_URI`: MongoDB connection string (e.g., `mongodb+srv://user:password@cluster.mongodb.net`)
   - `JWT_SECRET`: Your secret key for JWT signing
   - `CORS_ORIGINS`: Frontend URLs (comma-separated)

### Running Locally

\`\`\`bash
uvicorn app.main:app --reload
\`\`\`

Server will be available at `http://localhost:8000`

**API Documentation:** http://localhost:8000/docs (Swagger UI)

## API Endpoints

### Organizations

- `POST /org/create` - Create new organization
- `GET /org/get?organization_name={name}` - Get organization metadata
- `PUT /org/update` - Update organization (requires JWT)
- `DELETE /org/delete?organization_name={name}` - Delete organization (requires JWT)

### Authentication

- `POST /admin/login` - Admin login, returns JWT token

### Metrics

- `GET /metrics` - System metrics (org count, tenant collections)

## Example cURL Commands

### Create Organization
\`\`\`bash
curl -X POST http://localhost:8000/org/create \
  -H "Content-Type: application/json" \
  -d '{
    "organization_name": "acme",
    "email": "admin@acme.com",
    "password": "SecurePass123!"
  }'
\`\`\`

### Login
\`\`\`bash
curl -X POST http://localhost:8000/admin/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@acme.com",
    "password": "SecurePass123!"
  }'
\`\`\`

### Get Organization
\`\`\`bash
curl -X GET "http://localhost:8000/org/get?organization_name=acme"
\`\`\`

### Update Organization (Protected)
\`\`\`bash
curl -X PUT http://localhost:8000/org/update \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{
    "organization_name": "acme",
    "email": "newemail@acme.com"
  }'
\`\`\`

### Delete Organization (Protected)
\`\`\`bash
curl -X DELETE "http://localhost:8000/org/delete?organization_name=acme" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
\`\`\`

## MongoDB Setup

### Using MongoDB Atlas

1. Create account at [mongodb.com/atlas](https://mongodb.com/atlas)
2. Create a cluster
3. Get connection string
4. Set `MONGODB_URI` in `.env`:
   \`\`\`
   MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/?retryWrites=true&w=majority
   \`\`\`

### Using MongoDB Compass

Connect locally:
\`\`\`
mongodb://localhost:27017
\`\`\`

Inspect databases and collections created by SpiTen.

## Running the Demo

\`\`\`bash
python demo.py
\`\`\`

This will:
1. Create a test organization
2. Login as admin
3. Get organization metadata
4. Update organization
5. Delete organization

## Deployment

### Railway
1. Connect repository to Railway
2. Add MongoDB Atlas database
3. Set environment variables
4. Deploy

### Render
1. Create new Web Service
2. Connect GitHub repository
3. Build command: `pip install -r requirements.txt`
4. Start command: `uvicorn app.main:app --host 0.0.0.0 --port 8000`
5. Set environment variables
6. Deploy

### Docker
\`\`\`bash
docker build -t spiten-backend .
docker run -e MONGODB_URI=<your_uri> -e JWT_SECRET=<your_secret> -p 8000:8000 spiten-backend
\`\`\`

## Testing

Run pytest (requires MONGODB_TEST_URI in .env):
\`\`\`bash
pytest
\`\`\`

## Architecture

- **Services Layer**: `OrgService`, `AuthService` - Business logic
- **Routes**: Thin route handlers delegating to services
- **Database**: Motor async driver for MongoDB
- **Security**: bcrypt for hashing, JWT for tokens
- **Validation**: Pydantic models

## Notes

- MongoDB instance must be external (MongoDB Atlas recommended)
- JWT tokens expire after configured duration (default: 30 minutes)
- All passwords are hashed with bcrypt before storage
- Organization names are case-insensitive (lowercased in collections)
