# SPITEN — Smart Multi-Tenant Engine

[![GitHub](https://img.shields.io/badge/GitHub-Repository-181717?style=for-the-badge&logo=github&logoColor=white)](https://github.com/AseenaSulthana/SpiTen---Smart-Multi-Tenant-Engine.git)

A complete full-stack solution for multi-tenant organization management with Python FastAPI backend and modern static frontend.

![SPITEN](https://img.shields.io/badge/SPITEN-Multi--Tenant%20Engine-e91e63?style=for-the-badge)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![MongoDB](https://img.shields.io/badge/MongoDB-47A248?style=for-the-badge&logo=mongodb&logoColor=white)

## 🚀 Overview

SPITEN simplifies building multi-tenant applications by providing:

- **Dynamic Organization Management**: Create organizations and automatically generate isolated data collections
- **Dual Authentication System**: Separate login flows for organization admins and superadmins
- **Secure Authentication**: JWT-based authentication with bcrypt password hashing
- **Scalable Architecture**: FastAPI backend with MongoDB Atlas for unlimited tenant scaling
- **Modern UI**: Beautiful pink/white themed frontend with Inter font and professional design
- **Static Frontend**: Simple HTML/CSS/JS served directly from FastAPI

## 📁 Project Structure

```
spiten/
├── backend/                    # FastAPI application
│   ├── app.py                 # Main FastAPI app (consolidated)
│   ├── requirements.txt       # Python dependencies
│   ├── Dockerfile            # Docker configuration
│   ├── demo.py               # Demo script
│   └── postman_collection.json
│
├── frontend/                   # Static HTML/CSS/JS
│   ├── landing.html          # Public landing page
│   ├── login.html            # Login/Signup page (split layout)
│   ├── admin.html            # Superadmin dashboard
│   ├── user-dashboard.html   # Organization dashboard
│   ├── create-org.html       # Create organization
│   ├── get-org.html          # View organization
│   ├── update-org.html       # Update organization
│   ├── styles.css            # Main stylesheet
│   └── app.js                # API client & utilities
│
├── architecture_diagram.md    # System architecture
└── README.md                  # This file
```

## 🛠️ Tech Stack

### Backend
- **Framework**: FastAPI (Python 3.11+)
- **Database**: MongoDB Atlas (pymongo)
- **Authentication**: JWT (PyJWT) + bcrypt (passlib)
- **Server**: Uvicorn

### Frontend
- **Technologies**: HTML5, CSS3, JavaScript (ES6+)
- **Styling**: Custom CSS (Pink/White theme)
- **Font**: Inter (Google Fonts)
- **Icons**: Font Awesome 6

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- MongoDB Atlas account (or local MongoDB)

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/spiten.git
cd spiten

# Navigate to backend
cd backend

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the server
python app.py
```

### Access the Application

- **Landing Page**: http://localhost:8000/static/landing.html
- **API Docs**: http://localhost:8000/docs
- **Admin Panel**: http://localhost:8000/static/admin.html

### Default Superadmin Credentials
```
Email: admin@spiten.com
Password: admin123
```

## 🔐 Authentication

### Two Authentication Modes

| Mode | Endpoint | Access |
|------|----------|--------|
| **Organization** | `POST /admin/login` | User dashboard, own org only |
| **Superadmin** | `POST /superadmin/login` | Admin panel, all organizations |

### Login Page Features
- **Organisation Tab**: Sign In / Sign Up for organizations
- **Admin Tab**: Sign In only for superadmins
- Split-screen modern design

## 📡 API Endpoints

### Organizations (REST API)

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/organizations` | List all organizations | ✗ |
| POST | `/organizations` | Create new organization | ✗ |
| GET | `/organizations/{name}` | Get organization by name | ✗ |
| PUT | `/organizations/{name}` | Update organization | ✓ JWT |
| DELETE | `/organizations/{name}` | Delete organization | ✓ JWT |

### Authentication

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/admin/login` | Organization admin login |
| POST | `/superadmin/login` | Superadmin login |

### Metrics

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/metrics` | System metrics |

### Legacy Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/org/create` | Create organization |
| GET | `/org/get` | Get organization |
| PUT | `/org/update` | Update organization |
| DELETE | `/org/delete` | Delete organization |
| GET | `/org/list` | List organizations |

## 💻 Frontend Pages

| Page | Description |
|------|-------------|
| `landing.html` | Public landing page with hero, features, about sections |
| `login.html` | Split-screen login with Organisation/Admin tabs |
| `admin.html` | Superadmin dashboard - manage all organizations |
| `user-dashboard.html` | Organization dashboard - personalized for each org |
| `create-org.html` | Create new organization form |
| `get-org.html` | View organization details |
| `update-org.html` | Update organization settings |

## 🎨 Design Features

- **Theme**: Pink (#e91e63) and white color scheme
- **Font**: Inter (clean, modern typography)
- **Sidebar**: Professional gradient design with hover animations
- **Cards**: Soft shadows and rounded corners
- **Responsive**: Mobile-friendly layouts

## 🗄️ Database Schema

### Collections

```javascript
// organizations
{
  name: "acme",
  admin_email: "admin@acme.com",
  admin_password: "hashed_password",
  created_at: ISODate()
}

// admin_users
{
  organization_name: "acme",
  email: "admin@acme.com",
  password_hash: "bcrypt_hash"
}

// superadmins
{
  email: "admin@spiten.com",
  password_hash: "bcrypt_hash",
  role: "superadmin"
}

// Dynamic: org_{name}
// Each organization gets isolated collection
```

## 🔧 Environment Variables

Create `.env` file in backend directory:

```env
MONGODB_URI=mongodb+srv://user:pass@cluster.mongodb.net/
JWT_SECRET=your-secret-key-min-32-chars
```

## 📝 Example Usage

### Create Organization (Sign Up)

```bash
curl -X POST http://localhost:8000/organizations \
  -H "Content-Type: application/json" \
  -d '{
    "name": "acme",
    "admin_email": "admin@acme.com",
    "admin_password": "SecurePass123!"
  }'
```

### Login (Organization Admin)

```bash
curl -X POST http://localhost:8000/admin/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@acme.com",
    "password": "SecurePass123!"
  }'
```

### Login (Superadmin)

```bash
curl -X POST http://localhost:8000/superadmin/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@spiten.com",
    "password": "admin123"
  }'
```

## 🐳 Docker Deployment

```bash
cd backend
docker build -t spiten-backend .
docker run -e MONGODB_URI=<uri> -e JWT_SECRET=<secret> -p 8000:8000 spiten-backend
```

## 🔒 Security Features

- **Password Hashing**: bcrypt with passlib
- **JWT Tokens**: HS256 algorithm, 30-minute expiration
- **Role-based Access**: Organization admin vs Superadmin
- **Data Isolation**: Each organization has separate collection
- **CORS**: Configurable cross-origin settings

## 📊 Architecture

See [architecture_diagram.md](./architecture_diagram.md) for detailed system architecture.

## 🤝 Contributing

Contributions are welcome! Feel free to extend with:
- User roles and permissions
- Refresh tokens
- Email verification
- Organization invitation system
- Audit logging
- File upload support

## 📄 License

MIT License

## 👩‍💻 Author

**Built in AseeVerse❤️ by Aseena**

---

© 2025 SPITEN - Smart Multi-Tenant Engine
