# Backend API Documentation

## 1. General Information

**Base URL (Local Development):**

`http://127.0.0.1:8000`

**API Prefix:**

`/api/`

**Content-Type:**

`application/json`

## 2. Authentication

The API uses Token Authentication.

For authenticated requests, include the following header:

```http
Authorization: Token YOUR_AUTH_TOKEN
```

Replace `YOUR_AUTH_TOKEN` with the token returned by the Register or Login endpoint.

Do not use `Bearer`; the required format is `Token`.

---

# 3. User APIs

## 3.1 Register

**Endpoint:** `POST /api/users/register/`

**Authentication:** Not required.

**Request Body:**

```json
{
  "email": "user@example.com",
  "password": "password123",
  "username": "testuser"
}
```

Fields:

- `email`: Required. Must be unique.
- `password`: Required. Minimum 8 characters.
- `username`: Optional. If omitted, the email is used as the username.

**Success Response:** `201 Created`

```json
{
  "token": "YOUR_AUTH_TOKEN",
  "user": {
    "id": 1,
    "email": "user@example.com",
    "username": "testuser"
  }
}
```

## 3.2 Login

**Endpoint:** `POST /api/users/login/`

**Authentication:** Not required.

**Request Body:**

```json
{
  "email": "user@example.com",
  "password": "password123"
}
```

**Success Response:** `200 OK`

```json
{
  "token": "YOUR_AUTH_TOKEN",
  "user": {
    "id": 1,
    "email": "user@example.com",
    "username": "testuser"
  }
}
```

Invalid credentials return a validation error.

## 3.3 Get Current User

**Endpoint:** `GET /api/users/me/`

**Authentication:** Required.

**Success Response:** `200 OK`

```json
{
  "id": 1,
  "email": "user@example.com",
  "username": "testuser"
}
```

## 3.4 Logout

**Endpoint:** `POST /api/users/logout/`

**Authentication:** Required.

**Success Response:** `200 OK`

```json
{
  "message": "Successfully logged out."
}
```

The current authentication token is deleted after logout.

## 3.5 API Health Check

**Endpoint:** `GET /api/users/`

**Authentication:** Not required.

**Success Response:** `200 OK`

```json
{
  "message": "API is working!",
  "status": "success"
}
```

Other HTTP methods are not allowed and return `405 Method Not Allowed`.

---

# 4. Project APIs

## 4.1 List Projects

**Endpoint:** `GET /api/projects/`

**Authentication:** Not required.

Returns projects whose status is `open`.

**Optional Search Parameter:**

`?search=keyword`

Searches project titles.

**Example:**

```http
GET /api/projects/?search=python
```

**Success Response:** `200 OK`

Returns a list of projects using the Project response structure described below.

## 4.2 Create Project

**Endpoint:** `POST /api/projects/`

**Authentication:** Required.

**Request Body:**

```json
{
  "title": "Web Development Project",
  "goal": "Build a platform for students to collaborate on projects.",
  "description": "A project built with Django and React.",
  "capacity": 4,
  "status": "open",
  "skills": [1, 2]
}
```

Fields:

- `title`: Required. The project title.
- `goal`: Required. The main objective of the project.
- `description`: Optional. Additional information about the project.
- `capacity`: Required; minimum value is 1.
- `status`: Optional; accepted values are `open` and `closed`.
- `skills`: Optional; a list of existing Skill IDs.

The project creator is assigned automatically from the authenticated user. The client must not set the `creator` field.

**Success Response:** `201 Created`

Returns the created project, including its `goal` field.

## 4.3 Get Project Details

**Endpoint:** `GET /api/projects/{id}/`

**Authentication:** Not required.

Returns the details of the specified project.

**Success Response:** `200 OK`

```json
{
  "id": 5,
  "title": "Web Development Project",
  "goal": "Build a platform for students to collaborate on projects.",
  "description": "A project built with Django and React.",
  "creator": 1,
  "capacity": 4,
  "status": "open",
  "skills