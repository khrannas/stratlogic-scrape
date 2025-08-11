# Task 05: User Authentication System

## Overview
Implement a robust user authentication and authorization system using JWT (JSON Web Tokens). This task includes user registration, login, session management, and role-based access control (RBAC).

## Priority: High
## Estimated Time: 2-3 days
## Dependencies: Task 01, Task 02, Task 04

## Checklist

### 5.1 User Registration and Login
- [ ] Create endpoint for user registration (`/auth/register`)
- [ ] Implement password hashing for user credentials
- [ ] Create endpoint for user login (`/auth/login`) which returns a JWT
- [ ] Create endpoint for token refresh (`/auth/refresh`)

### 5.2 JWT Authentication
- [ ] Generate JWTs upon successful login
- [ ] Create a dependency to verify JWTs from request headers
- [ ] Implement token expiration and revocation
- [ ] Store JWT secret key securely in configuration

### 5.3 Role-Based Access Control (RBAC)
- [ ] Define user roles (e.g., admin, user) in the user model
- [ ] Create a dependency to check for required user roles on protected endpoints
- [ ] Secure sensitive endpoints to be accessible only by specific roles

### 5.4 Session Management
- [ ] Implement a mechanism for users to log out
- [ ] (Optional) Implement a token blocklist for immediate token invalidation on logout.

## Subtasks

### Subtask 5.1.1: Password Hashing
- Use a strong hashing algorithm like `bcrypt` or `argon2`.
- The `passlib` library is a good choice for this.

### Subtask 5.2.1: JWT Generation and Verification
- Use a library like `python-jose` to create and verify JWTs.
- The token payload should include user ID, roles, and expiration time (`exp`).

### Subtask 5.3.1: RBAC Dependency
- Create a reusable FastAPI dependency `(Depends(...))` that can be applied to endpoints requiring specific roles.
- The dependency should decode the JWT, extract the user's roles, and check if they meet the requirements.

## Files to Create

1.  `src/api/routers/auth.py` - Endpoints for authentication (register, login, refresh).
2.  `src/core/security.py` - Functions for password hashing, JWT creation, and verification.
3.  `src/api/dependencies/auth.py` - Dependencies for getting the current user and checking roles.
4.  `src/api/schemas/auth_schemas.py` - Pydantic schemas for registration, login, and tokens.
5.  `src/services/user_service.py` - Business logic for user creation and authentication.
6.  Update `src/core/models.py` to include user roles.

## Testing

### Unit Tests
- [ ] Test user registration with valid and invalid data.
- [ ] Test user login with correct and incorrect credentials.
- [ ] Test that the login endpoint returns a valid JWT.
- [ ] Test that protected endpoints return 401/403 errors for unauthenticated or unauthorized users.
- [ ] Test the role-based access control dependency.
- [ ] Test password hashing and verification logic.

## Documentation

- [ ] Document the authentication flow.
- [ ] Update the API documentation to show which endpoints are protected and what roles are required.
- [ ] Provide examples of how to include the JWT in the `Authorization` header.

## Risk Assessment and Mitigation

### High Risk Items

#### 1. Security of JWTs
**Risk**: Improper handling of JWTs can lead to account takeover.
**Mitigation Strategies**:
-   **Use a strong secret key**: The secret key should be long, random, and stored securely (e.g., environment variable or secrets manager).
-   **Use a strong algorithm**: Use HS256 or stronger. Avoid `none` algorithm.
-   **Set short expiration times**: Keep token lifetimes short (e.g., 15 minutes) and use refresh tokens for longer sessions.
-   **Transmit over HTTPS**: Always transmit tokens over a secure channel.

#### 2. Credential Security
**Risk**: Storing passwords insecurely can lead to massive data breaches.
**Mitigation Strategies**:
-   **Never store plain-text passwords**: Use a strong, salted hashing algorithm.
-   **Protect against timing attacks**: Use a constant-time comparison function for password hashes. `passlib` handles this automatically.

## Next Steps

After completing this task, subsequent tasks like the scrapers can integrate with the user system to associate jobs with users.

## Completion Criteria

- [ ] User registration and login functionality is complete and secure.
- [ ] API endpoints are protected using JWT authentication.
- [ ] Role-based access control is implemented and functional.
- [ ] The system is tested for common authentication and authorization vulnerabilities.
