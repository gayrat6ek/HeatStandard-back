# User Authentication and Authorization

## Overview

All API endpoints (except `/health`, `/`, and `/auth/login`) now require JWT token authentication.

## Authentication Flow

1. **Login**: POST `/api/v1/auth/login` with username and password
2. **Receive Token**: Get JWT access token in response
3. **Use Token**: Include token in `Authorization: Bearer <token>` header for all requests

## User Roles

- **Admin**: Full access to all endpoints, can manage users
- **User**: Access to all endpoints except user management

## Protected Endpoints

### Authentication Required (Any authenticated user)

All endpoints require a valid JWT token:

- **Organizations**: GET, POST /sync
- **Products**: GET, POST /sync
- **Terminal Groups**: GET, POST /sync
- **Sections**: GET, POST /sync
- **Orders**: GET, POST (create orders)

### Admin Only Endpoints

These endpoints require admin role:

- **Users Management**:
  - GET `/api/v1/users` - List all users
  - POST `/api/v1/users` - Create user
  - PUT `/api/v1/users/{id}` - Update user
  - DELETE `/api/v1/users/{id}` - Delete user

### Public Endpoints (No authentication required)

- `GET /` - Root endpoint
- `GET /health` - Health check
- `POST /api/v1/auth/login` - Login
- `GET /docs` - API documentation
- `GET /redoc` - API documentation (ReDoc)

## Usage Examples

### 1. Login

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "admin123"
  }'
```

Response:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

### 2. Use Token in Requests

```bash
# Get organizations
curl -X GET http://localhost:8000/api/v1/organizations \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."

# Create order
curl -X POST http://localhost:8000/api/v1/orders \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -H "Content-Type: application/json" \
  -d '{...}'
```

### 3. Get Current User Info

```bash
curl -X GET http://localhost:8000/api/v1/users/me \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

## Creating First Admin User

After running migrations, you'll need to create the first admin user. You can do this via a script or directly in the database:

### Option 1: Using Python Script

Create `app/scripts/create_admin.py`:

```python
from app.database import SessionLocal
from app.crud.user import create_user
from app.schemas.user import UserCreate
from app.models.user import UserRole

db = SessionLocal()

admin_user = UserCreate(
    email="admin@example.com",
    username="admin",
    full_name="System Administrator",
    password="admin123",  # Change this!
    role=UserRole.ADMIN
)

user = create_user(db, admin_user)
print(f"Admin user created: {user.username}")
db.close()
```

Run: `docker-compose exec app python -m app.scripts.create_admin`

### Option 2: Using SQL

```sql
-- Connect to database
docker-compose exec db psql -U postgres -d iiko_db

-- Insert admin user (password is 'admin123' hashed with bcrypt)
INSERT INTO users (id, email, username, full_name, hashed_password, role, is_active)
VALUES (
  gen_random_uuid(),
  'admin@example.com',
  'admin',
  'System Administrator',
  '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5NU7LdqOA7Bqm',
  'admin',
  true
);
```

## Token Expiration

- Access tokens expire after 30 minutes
- After expiration, users must login again to get a new token
- Token expiration time can be configured in `app/utils/auth.py`

## Error Responses

### 401 Unauthorized
```json
{
  "detail": "Could not validate credentials"
}
```

### 403 Forbidden
```json
{
  "detail": "Not enough permissions. Admin role required."
}
```

## Security Best Practices

1. **Change SECRET_KEY**: Update `SECRET_KEY` in `.env` to a secure random string
   ```bash
   openssl rand -hex 32
   ```

2. **Use HTTPS**: In production, always use HTTPS to protect tokens in transit

3. **Token Storage**: Store tokens securely on the client side (e.g., httpOnly cookies or secure storage)

4. **Password Policy**: Enforce strong passwords (minimum 6 characters currently)

5. **Regular Token Rotation**: Consider implementing refresh tokens for better security
