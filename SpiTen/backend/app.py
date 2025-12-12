from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
import uvicorn
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import os
import pymongo
from pymongo.errors import ServerSelectionTimeoutError
import mongomock
from passlib.context import CryptContext
import jwt

# Config (override with env vars)
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("MASTER_DB_NAME", "spiten_master")
JWT_SECRET = os.getenv("JWT_SECRET", "change_this_secret")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRES_MINUTES", "30"))

# Setup DB (synchronous pymongo used for simplicity)
use_mock = os.getenv("USE_MOCK_DB", "0") == "1"
if use_mock:
    client = mongomock.MongoClient()
else:
    try:
        client = pymongo.MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
        # trigger server selection to verify connection
        client.admin.command('ping')
    except ServerSelectionTimeoutError:
        # fallback to in-memory mongomock for demo if MongoDB is unreachable
        client = mongomock.MongoClient()

db = client[DB_NAME]
orgs_col = db["organizations"]
admin_col = db["admin_users"]
metrics_col = db["_metrics"]

# Password hashing
pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")

app = FastAPI(title="SPITEN Consolidated API")

# Add CORS middleware FIRST before any routes/mounts
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=False,  # Must be False when using allow_origins=["*"]
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
)

# Serve the static frontend from the repository's frontend folder under /static
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", "frontend"))
if os.path.isdir(FRONTEND_DIR):
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")

# Schemas
class OrgCreate(BaseModel):
    organization_name: str = Field(..., min_length=1)
    email: EmailStr
    password: str = Field(..., min_length=6)

class OrgUpdate(BaseModel):
    organization_name: str = Field(..., min_length=1)
    new_organization_name: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = Field(None, min_length=6)

class LoginIn(BaseModel):
    email: EmailStr
    password: str

# Helpers
def hash_password(password: str) -> str:
    return pwd_ctx.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    try:
        return pwd_ctx.verify(plain, hashed)
    except Exception:
        return False

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire, "iat": datetime.utcnow()})
    return jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)

def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

def require_auth(authorization: Optional[str] = Header(None)) -> dict:
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization header")
    if not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization scheme")
    token = authorization.split(" ", 1)[1]
    return decode_token(token)

# Routes
@app.get("/")
def root():
    # Redirect root to the static landing page if it exists
    landing = "/static/landing.html"
    if os.path.isdir(FRONTEND_DIR) and os.path.exists(os.path.join(FRONTEND_DIR, "landing.html")):
        return RedirectResponse(landing)
    return {"message": "SpiTen - Consolidated API", "status": "running", "docs": "/docs"}

@app.post("/org/create", status_code=201)
def create_org(payload: OrgCreate):
    if orgs_col.find_one({"organization_name": payload.organization_name}):
        raise HTTPException(status_code=409, detail="Organization already exists")
    now = datetime.utcnow()
    org_doc = {
        "organization_name": payload.organization_name,
        "email": payload.email,
        "collection_name": f"org_{payload.organization_name.lower()}",
        "created_at": now,
        "updated_at": now,
    }
    res = orgs_col.insert_one(org_doc)
    # create admin user
    admin_doc = {
        "organization_name": payload.organization_name,
        "email": payload.email,
        "password_hash": hash_password(payload.password),
        "created_at": now,
    }
    admin_col.insert_one(admin_doc)
    return {"status": "success", "message": "Organization created", "data": {"organization_name": payload.organization_name, "email": payload.email, "id": str(res.inserted_id)}}

@app.get("/org/get")
def get_org(organization_name: str):
    org = orgs_col.find_one({"organization_name": organization_name})
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    org.pop("_id", None)
    org.pop("password_hash", None)
    return {"status": "success", "data": org}

@app.get("/org/list")
def list_orgs():
    docs = list(orgs_col.find({}, {"password_hash": 0}))
    for d in docs:
        d["id"] = str(d.pop("_id", ""))
    return {"status": "success", "data": docs}

@app.put("/org/update")
def update_org(payload: OrgUpdate, token_payload: dict = Depends(require_auth)):
    org = orgs_col.find_one({"organization_name": payload.organization_name})
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    update_fields: Dict[str, Any] = {}
    if payload.email:
        update_fields["email"] = payload.email
    if payload.password:
        update_fields["updated_at"] = datetime.utcnow()
        # update admin password
        admin_col.update_many({"organization_name": payload.organization_name}, {"$set": {"password_hash": hash_password(payload.password)}})
    if payload.new_organization_name:
        update_fields["organization_name"] = payload.new_organization_name
        update_fields["collection_name"] = f"org_{payload.new_organization_name.lower()}"
        admin_col.update_many({"organization_name": payload.organization_name}, {"$set": {"organization_name": payload.new_organization_name}})
    if update_fields:
        update_fields["updated_at"] = datetime.utcnow()
        orgs_col.update_one({"organization_name": payload.organization_name}, {"$set": update_fields})
    updated = orgs_col.find_one({"organization_name": update_fields.get("organization_name", payload.organization_name)})
    updated.pop("_id", None)
    return {"status": "success", "data": updated}

@app.delete("/org/delete")
def delete_org(organization_name: str, token_payload: dict = Depends(require_auth)):
    res = orgs_col.delete_one({"organization_name": organization_name})
    admin_col.delete_many({"organization_name": organization_name})
    if res.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Organization not found")
    return {"status": "success", "message": f"Organization '{organization_name}' deleted"}

@app.post("/admin/login")
def admin_login(payload: LoginIn):
    admin = admin_col.find_one({"email": payload.email})
    if not admin or not verify_password(payload.password, admin.get("password_hash", "")):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_access_token({"admin_id": str(admin.get("_id")), "organization_name": admin.get("organization_name")})
    return {"status": "success", "data": {"access_token": token, "admin_id": str(admin.get("_id")), "organization_name": admin.get("organization_name")}}

# Superadmin collection for admin panel access
superadmin_col = db["superadmins"]

# Create default superadmin if not exists
def ensure_superadmin():
    if superadmin_col.count_documents({}) == 0:
        superadmin_col.insert_one({
            "email": "admin@spiten.com",
            "password_hash": hash_password("admin123"),
            "role": "superadmin",
            "created_at": datetime.utcnow()
        })

# Call on startup
ensure_superadmin()

@app.post("/superadmin/login")
def superadmin_login(payload: LoginIn):
    """Login for superadmin to access admin panel."""
    admin = superadmin_col.find_one({"email": payload.email})
    if not admin or not verify_password(payload.password, admin.get("password_hash", "")):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_access_token({"superadmin_id": str(admin.get("_id")), "role": "superadmin"})
    return {"status": "success", "data": {"access_token": token, "role": "superadmin", "email": admin.get("email")}}

def require_superadmin(authorization: Optional[str] = Header(None)) -> dict:
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization header")
    if not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization scheme")
    token = authorization.split(" ", 1)[1]
    payload = decode_token(token)
    if payload.get("role") != "superadmin":
        raise HTTPException(status_code=403, detail="Superadmin access required")
    return payload

# ================== REST API: /organizations ==================
@app.get("/organizations")
def list_organizations():
    """List all organizations."""
    docs = list(orgs_col.find({}, {"password_hash": 0}))
    for d in docs:
        d["id"] = str(d.pop("_id", ""))
        # Normalize field names
        if "organization_name" in d:
            d["name"] = d.get("organization_name")
        if "email" in d:
            d["admin_email"] = d.get("email")
    return {"status": "success", "data": {"organizations": docs}}

@app.post("/organizations", status_code=201)
def create_organization(payload: dict):
    """Create a new organization."""
    name = payload.get("name") or payload.get("organization_name")
    email = payload.get("admin_email") or payload.get("email")
    password = payload.get("password")
    
    if not name or not email or not password:
        raise HTTPException(status_code=400, detail="name, admin_email/email, and password are required")
    
    if orgs_col.find_one({"organization_name": name}):
        raise HTTPException(status_code=409, detail="Organization already exists")
    
    now = datetime.utcnow()
    org_doc = {
        "organization_name": name,
        "email": email,
        "collection_name": f"org_{name.lower().replace('-', '_').replace(' ', '_')}",
        "created_at": now,
        "updated_at": now,
    }
    res = orgs_col.insert_one(org_doc)
    
    # Create admin user for the org
    admin_doc = {
        "organization_name": name,
        "email": email,
        "password_hash": hash_password(password),
        "created_at": now,
    }
    admin_col.insert_one(admin_doc)
    
    return {"status": "success", "message": "Organization created", "data": {"name": name, "admin_email": email, "id": str(res.inserted_id)}}

@app.get("/organizations/{name}")
def get_organization(name: str):
    """Get organization by name."""
    org = orgs_col.find_one({"organization_name": name})
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    org["id"] = str(org.pop("_id", ""))
    org["name"] = org.get("organization_name")
    org["admin_email"] = org.get("email")
    org.pop("password_hash", None)
    return {"status": "success", "data": {"organization": org}}

@app.put("/organizations/{name}")
def update_organization(name: str, payload: dict):
    """Update organization."""
    org = orgs_col.find_one({"organization_name": name})
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    
    update_fields = {"updated_at": datetime.utcnow()}
    
    new_name = payload.get("name") or payload.get("new_organization_name")
    new_email = payload.get("admin_email") or payload.get("email")
    new_password = payload.get("password")
    
    if new_email:
        update_fields["email"] = new_email
    if new_name:
        update_fields["organization_name"] = new_name
        update_fields["collection_name"] = f"org_{new_name.lower().replace('-', '_').replace(' ', '_')}"
        admin_col.update_many({"organization_name": name}, {"$set": {"organization_name": new_name}})
    if new_password:
        admin_col.update_many({"organization_name": name}, {"$set": {"password_hash": hash_password(new_password)}})
    
    orgs_col.update_one({"organization_name": name}, {"$set": update_fields})
    
    updated_name = new_name or name
    updated = orgs_col.find_one({"organization_name": updated_name})
    updated["id"] = str(updated.pop("_id", ""))
    updated["name"] = updated.get("organization_name")
    updated["admin_email"] = updated.get("email")
    
    return {"status": "success", "data": {"organization": updated}}

@app.delete("/organizations/{name}")
def delete_organization(name: str):
    """Delete organization."""
    res = orgs_col.delete_one({"organization_name": name})
    admin_col.delete_many({"organization_name": name})
    if res.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Organization not found")
    return {"status": "success", "message": f"Organization '{name}' deleted"}

@app.get("/metrics")
def metrics():
    org_count = orgs_col.count_documents({})
    admin_count = admin_col.count_documents({})
    superadmin_count = superadmin_col.count_documents({})
    snapshot = {"organizations": org_count, "admins": admin_count, "superadmins": superadmin_count, "timestamp": datetime.utcnow().isoformat()}
    metrics_col.insert_one({"snapshot": snapshot, "ts": datetime.utcnow()})
    return {"status": "success", "data": snapshot}

@app.post("/seed-demo-data")
def seed_demo_data():
    """Seed database with demo organizations for testing."""
    demo_orgs = [
        {"organization_name": "acme-corp", "email": "admin@acme-corp.com", "password": "Demo@123"},
        {"organization_name": "techstart-io", "email": "contact@techstart.io", "password": "Demo@123"},
        {"organization_name": "globalsoft", "email": "info@globalsoft.com", "password": "Demo@123"},
        {"organization_name": "innovate-labs", "email": "hello@innovate-labs.com", "password": "Demo@123"},
        {"organization_name": "cloudnine-systems", "email": "support@cloudnine.systems", "password": "Demo@123"},
    ]
    created = []
    skipped = []
    for org in demo_orgs:
        if orgs_col.find_one({"organization_name": org["organization_name"]}):
            skipped.append(org["organization_name"])
            continue
        now = datetime.utcnow()
        org_doc = {
            "organization_name": org["organization_name"],
            "email": org["email"],
            "collection_name": f"org_{org['organization_name'].replace('-', '_')}",
            "created_at": now,
            "updated_at": now,
        }
        orgs_col.insert_one(org_doc)
        admin_doc = {
            "organization_name": org["organization_name"],
            "email": org["email"],
            "password_hash": hash_password(org["password"]),
            "created_at": now,
        }
        admin_col.insert_one(admin_doc)
        created.append(org["organization_name"])
    return {
        "status": "success",
        "message": f"Demo data seeded: {len(created)} created, {len(skipped)} skipped (already exist)",
        "data": {"created": created, "skipped": skipped}
    }


if __name__ == "__main__":
    # Run the app with uvicorn when executed directly: python app.py
    uvicorn.run("app:app", host="0.0.0.0", port=int(os.getenv("PORT", 8000)), reload=True)
