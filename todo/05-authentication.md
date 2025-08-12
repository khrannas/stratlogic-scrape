# Task 05: User Authentication System

## Overview
Implement a robust user authentication and authorization system using JWT (JSON Web Tokens). This task includes user registration, login, session management, and role-based access control (RBAC).

## Priority: High
## Estimated Time: 2-3 days
## Dependencies: Task 01, Task 02, Task 04
## Status: ✅ Completed

## Checklist

### 5.1 User Registration and Login
- [x] Create endpoint for user registration (`/auth/register`)
- [x] Implement password hashing for user credentials
- [x] Create endpoint for user login (`/auth/login`) which returns a JWT
- [x] Create endpoint for token refresh (`/auth/refresh`)

### 5.2 JWT Authentication
- [x] Generate JWTs upon successful login
- [x] Create a dependency to verify JWTs from request headers
- [x] Implement token expiration and revocation
- [x] Store JWT secret key securely in configuration

### 5.3 Role-Based Access Control (RBAC)
- [x] Define user roles (e.g., admin, user) in the user model
- [x] Create a dependency to check for required user roles on protected endpoints
- [x] Secure sensitive endpoints to be accessible only by specific roles

### 5.4 Session Management
- [x] Implement a mechanism for users to log out
- [x] (Optional) Implement a token blocklist for immediate token invalidation on logout.

## Subtasks

### Subtask 5.1.1: Password Hashing ✅
- Use a strong hashing algorithm like `bcrypt` or `argon2`.
- The `passlib` library is a good choice for this.

### Subtask 5.2.1: JWT Generation and Verification ✅
- Use a library like `python-jose` to create and verify JWTs.
- The token payload should include user ID, roles, and expiration time (`exp`).

### Subtask 5.3.1: RBAC Dependency ✅
- Create a reusable FastAPI dependency `(Depends(...))` that can be applied to endpoints requiring specific roles.
- The dependency should decode the JWT, extract the user's roles, and check if they meet the requirements.

## Files Created

1. ✅ `src/core/security.py` - Extended with JWT functions for token creation and verification
2. ✅ `src/api/schemas/auth_schemas.py` - Pydantic schemas for authentication requests and responses
3. ✅ `src/services/user_service.py` - Business logic for user authentication and management
4. ✅ `src/api/dependencies/auth.py` - Dependencies for authentication and authorization
5. ✅ `src/api/routers/auth.py` - Authentication endpoints (register, login, logout, etc.)
6. ✅ `tests/api/test_auth.py` - Comprehensive tests for authentication system
7. ✅ Updated `src/core/exceptions.py` - Added authentication-related exceptions
8. ✅ Updated `src/main.py` - Added authentication router to the application

## Implementation Details

### Authentication Endpoints
- `POST /api/v1/auth/register` - User registration
- `POST /api/v1/auth/login` - User login with JWT token response
- `GET /api/v1/auth/me` - Get current user information
- `POST /api/v1/auth/logout` - User logout
- `PUT /api/v1/auth/users/{user_id}/role` - Update user role (admin only)
- `PUT /api/v1/auth/users/{user_id}/deactivate` - Deactivate user (admin only)
- `PUT /api/v1/auth/users/{user_id}/activate` - Activate user (admin only)

### Security Features
- **Password Hashing**: Using bcrypt via passlib
- **JWT Tokens**: Using python-jose with HS256 algorithm
- **Token Expiration**: Configurable via settings
- **Role-Based Access Control**: Admin, user, and custom role support
- **Input Validation**: Comprehensive Pydantic validation
- **Error Handling**: Custom exceptions with proper HTTP status codes

### Dependencies Available
- `get_current_user` - Get authenticated user from JWT
- `get_current_active_user` - Get active authenticated user
- `require_admin` - Require admin role
- `require_role(role)` - Require specific role
- `require_user_or_admin(user_id)` - Require user themselves or admin

## Testing

### Unit Tests ✅
- [x] Test user registration with valid and invalid data.
- [x] Test user login with correct and incorrect credentials.
- [x] Test that the login endpoint returns a valid JWT.
- [x] Test that protected endpoints return 401/403 errors for unauthenticated or unauthorized users.
- [x] Test the role-based access control dependency.
- [x] Test password hashing and verification logic.

## Documentation

- [x] Document the authentication flow.
- [x] Update the API documentation to show which endpoints are protected and what roles are required.
- [x] Provide examples of how to include the JWT in the `Authorization` header.

## Risk Assessment and Mitigation

### High Risk Items

#### 1. Security of JWTs ✅
**Risk**: Improper handling of JWTs can lead to account takeover.
**Mitigation Strategies**:
-   **Use a strong secret key**: The secret key should be long, random, and stored securely (e.g., environment variable or secrets manager).
-   **Use a strong algorithm**: Use HS256 or stronger. Avoid `none` algorithm.
-   **Set short expiration times**: Keep token lifetimes short (e.g., 15 minutes) and use refresh tokens for longer sessions.
-   **Transmit over HTTPS**: Always transmit tokens over a secure channel.

#### 2. Credential Security ✅
**Risk**: Storing passwords insecurely can lead to massive data breaches.
**Mitigation Strategies**:
-   **Never store plain-text passwords**: Use a strong, salted hashing algorithm.
-   **Protect against timing attacks**: Use a constant-time comparison function for password hashes. `passlib` handles this automatically.

## Next Steps

After completing this task, subsequent tasks like the scrapers can integrate with the user system to associate jobs with users.

## Completion Criteria

- [x] User registration and login functionality is complete and secure.
- [x] API endpoints are protected using JWT authentication.
- [x] Role-based access control is implemented and functional.
- [x] The system is tested for common authentication and authorization vulnerabilities.

## API Usage Examples

### Register a new user:
```bash
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "username": "testuser",
    "password": "securepassword123",
    "full_name": "Test User"
  }'
```

### Login and get JWT token:
```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "securepassword123"
  }'
```

### Access protected endpoint:
```bash
curl -X GET "http://localhost:8000/api/v1/auth/me" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

## Files Modified
- `src/core/security.py` - Added JWT functionality
- `src/core/exceptions.py` - Added authentication exceptions
- `src/main.py` - Added auth router
- `src/services/user_service.py` - Updated with authentication logic
