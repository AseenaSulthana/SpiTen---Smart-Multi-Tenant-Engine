# SPITEN Architecture Diagram

## System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                     CLIENT BROWSER                              │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  Static Frontend (HTML/CSS/JS)                            │  │
│  │  ├─ landing.html      (Public landing page)               │  │
│  │  ├─ login.html        (Organization & Admin login/signup) │  │
│  │  ├─ admin.html        (Superadmin dashboard)              │  │
│  │  ├─ user-dashboard.html (Organization dashboard)          │  │
│  │  ├─ create-org.html   (Create organization)               │  │
│  │  ├─ get-org.html      (View organization)                 │  │
│  │  ├─ update-org.html   (Update organization)               │  │
│  │  ├─ styles.css        (Pink/white theme, Inter font)      │  │
│  │  └─ app.js            (API client & utilities)            │  │
│  └──────────────────┬──────────────────────────────────────┘  │
└─────────────────────┼──────────────────────────────────────────┘
                      │ HTTP (served from FastAPI /static)
                      │
┌─────────────────────▼──────────────────────────────────────────┐
│                  API LAYER (FastAPI)                           │
│  ┌────────────────────────────────────────────────────────┐   │
│  │ Routes (app.py - Consolidated)                         │   │
│  │                                                        │   │
│  │ Organizations (REST API):                              │   │
│  │ ├─ GET  /organizations         (list all)             │   │
│  │ ├─ POST /organizations         (create org)           │   │
│  │ ├─ GET  /organizations/{name}  (get org)              │   │
│  │ ├─ PUT  /organizations/{name}  (update org)           │   │
│  │ └─ DELETE /organizations/{name} (delete org)          │   │
│  │                                                        │   │
│  │ Authentication:                                        │   │
│  │ ├─ POST /admin/login           (org admin login)      │   │
│  │ └─ POST /superadmin/login      (superadmin login)     │   │
│  │                                                        │   │
│  │ Legacy Endpoints:                                      │   │
│  │ ├─ POST /org/create, GET /org/get, etc.               │   │
│  │ └─ GET /metrics                                        │   │
│  └──────────────────┬─────────────────────────────────────┘   │
│                     │                                          │
│  ┌──────────────────▼─────────────────────────────────────┐   │
│  │ Security & Utils                                       │   │
│  │ ├─ hash_password() → bcrypt                           │   │
│  │ ├─ verify_password() → bcrypt                         │   │
│  │ ├─ create_access_token() → PyJWT                      │   │
│  │ ├─ get_current_admin() → JWT verification             │   │
│  │ └─ require_superadmin() → Superadmin auth             │   │
│  └──────────────────┬─────────────────────────────────────┘   │
└─────────────────────┼──────────────────────────────────────────┘
                      │ MongoDB (pymongo)
                      │
┌─────────────────────▼──────────────────────────────────────────┐
│            MONGODB ATLAS                                       │
│  ┌────────────────────────────────────────────────────────┐   │
│  │ Database: spiten_db                                    │   │
│  │                                                        │   │
│  │ ├─ organizations collection                            │   │
│  │ │  └─ { name, admin_email, admin_password, created_at }│   │
│  │ │                                                      │   │
│  │ ├─ admin_users collection                              │   │
│  │ │  └─ { organization_name, email, password_hash }      │   │
│  │ │                                                      │   │
│  │ ├─ superadmins collection                              │   │
│  │ │  └─ { email, password_hash, role: "superadmin" }     │   │
│  │ │                                                      │   │
│  │ └─ _metrics collection                                 │   │
│  │    └─ { api_calls, orgs_created, orgs_deleted, ... }   │   │
│  └────────────────────────────────────────────────────────┘   │
│                                                                │
│  ┌────────────────────────────────────────────────────────┐   │
│  │ Dynamic Tenant Collections (per organization)          │   │
│  │ ├─ org_acme        (isolated data for ACME org)       │   │
│  │ ├─ org_techcorp    (isolated data for TechCorp org)   │   │
│  │ └─ org_{name}      (one collection per organization)  │   │
│  └────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

## User Authentication Flow

### Organization Sign Up Flow

```
Frontend (login.html - Sign Up mode)
    │
    ├─ User enters: Organization Name, Email, Password, Confirm Password
    │
    ├─ POST /organizations
    │   └─ { name, admin_email, admin_password }
    │
API (app.py)
    │
    ├─ Check uniqueness of organization name
    ├─ Hash password with bcrypt
    ├─ Create organization document
    ├─ Create admin user document
    └─ Create dynamic collection org_{name}
    │
    ├─ Auto-login: POST /admin/login
    │   └─ Returns JWT token
    │
Frontend
    │
    ├─ Store token in localStorage
    └─ Redirect to user-dashboard.html
```

### Organization Sign In Flow

```
Frontend (login.html - Sign In mode, Organisation tab)
    │
    ├─ User enters: Email, Password
    │
    ├─ POST /admin/login
    │   └─ { email, password }
    │
API (app.py)
    │
    ├─ Find admin user by email
    ├─ Verify password with bcrypt
    └─ Create JWT token (includes admin_id, org_name, exp)
    │
Frontend
    │
    ├─ Store token & org_name in localStorage
    └─ Redirect to user-dashboard.html
```

### Superadmin Sign In Flow

```
Frontend (login.html - Admin tab)
    │
    ├─ User enters: Email, Password
    │   Default: admin@spiten.com / admin123
    │
    ├─ POST /superadmin/login
    │   └─ { email, password }
    │
API (app.py)
    │
    ├─ Find superadmin by email
    ├─ Verify password with bcrypt
    └─ Create JWT token (role: superadmin)
    │
Frontend
    │
    ├─ Store token & admin_role in localStorage
    └─ Redirect to admin.html
```

## Page Structure

```
Landing Page (landing.html)
├─ Navigation (Home, Features, About, Login)
├─ Hero Section
│  ├─ Title & Description
│  ├─ CTA Buttons (Login, Admin Panel)
│  └─ Dashboard Preview Card
├─ Features Section (Quick Actions)
│  ├─ Create Organization
│  ├─ Get Organization
│  └─ Update Organization
├─ About Section
│  ├─ About SPITEN description
│  └─ Feature Cards (Secure, Fast, Developer First)
├─ CTA Section
└─ Footer (© 2025 | Built in AseeVerse❤️ by Aseena)

Login Page (login.html)
├─ Split Layout
│  ├─ Left Panel (Pink gradient)
│  │  ├─ SPITEN Logo
│  │  ├─ Organisation Tab
│  │  ├─ Admin Tab
│  │  └─ Sign In / Sign Up Toggle (org only)
│  └─ Right Panel (White)
│     ├─ User Avatar Icon
│     ├─ Form Title
│     ├─ Input Fields (dynamic based on mode)
│     ├─ Submit Button
│     └─ Social Login (Google, Facebook)

Admin Dashboard (admin.html)
├─ Sidebar Navigation
│  ├─ Dashboard
│  ├─ Create Org
│  ├─ Find Org
│  ├─ Settings
│  └─ Logout
├─ Header (Search, Refresh, Notifications)
├─ Welcome Banner
├─ Stats Cards (Total Orgs, Active, API Calls)
├─ Organizations Table
└─ Requires superadmin authentication

User Dashboard (user-dashboard.html)
├─ Sidebar Navigation
│  ├─ Dashboard
│  ├─ Analytics
│  ├─ Team
│  ├─ Reports
│  ├─ Settings
│  └─ Logout
├─ Header (Search, Notifications)
├─ Welcome Banner (personalized)
├─ Stats Cards (Members, Projects, Tasks)
├─ Quick Actions Grid
└─ Requires organization authentication
```

## Security Model

```
┌────────────────────────────────────────────────────────────┐
│                    AUTHENTICATION                          │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  Organization Admin                 Superadmin             │
│  ┌────────────────────┐            ┌────────────────────┐  │
│  │ POST /admin/login  │            │ POST /superadmin/  │  │
│  │                    │            │      login         │  │
│  │ Scope:             │            │                    │  │
│  │ - Own org only     │            │ Scope:             │  │
│  │ - user-dashboard   │            │ - All organizations│  │
│  │                    │            │ - admin.html       │  │
│  └────────────────────┘            └────────────────────┘  │
│                                                            │
├────────────────────────────────────────────────────────────┤
│                    PASSWORD SECURITY                       │
├────────────────────────────────────────────────────────────┤
│  • Hashed with bcrypt (passlib)                           │
│  • Never stored in plain text                              │
│  • Default superadmin created on startup                   │
│                                                            │
├────────────────────────────────────────────────────────────┤
│                    JWT TOKENS                              │
├────────────────────────────────────────────────────────────┤
│  • Algorithm: HS256                                        │
│  • Expiration: 30 minutes                                  │
│  • Payload: { admin_id, organization_name, role, exp }     │
│  • Stored in localStorage                                  │
└────────────────────────────────────────────────────────────┘
```

## Running the Application

```
Backend (FastAPI + Static Files)
│
├─ cd backend
├─ python -m venv .venv
├─ .venv\Scripts\activate
├─ pip install -r requirements.txt
├─ python app.py
│
└─ Server running at http://localhost:8000
   ├─ API: http://localhost:8000/docs
   └─ Frontend: http://localhost:8000/static/landing.html
```

## Tech Stack

| Layer | Technology |
|-------|------------|
| Frontend | HTML5, CSS3, JavaScript (ES6+) |
| Styling | Custom CSS (Pink/White theme, Inter font) |
| Icons | Font Awesome 6 |
| Backend | FastAPI (Python 3.11+) |
| Database | MongoDB Atlas |
| Auth | JWT (PyJWT) + bcrypt (passlib) |
| Server | Uvicorn |
