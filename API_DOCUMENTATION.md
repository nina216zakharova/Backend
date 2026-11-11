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
  "description": "A project built with Django and React.",
  "capacity": 4,
  "status": "open",
  "skills": [1, 2]
}
```

Fields:

- `title`: Required.
- `description`: Optional.
- `capacity`: Required; minimum value is 1.
- `status`: Optional; accepted values are `open` and `closed`.
- `skills`: Optional; a list of existing Skill IDs.

The project creator is assigned automatically from the authenticated user. The client must not set the `creator` field.

**Success Response:** `201 Created`

Returns the created project.

## 4.3 Get Project Details

**Endpoint:** `GET /api/projects/{id}/`

**Authentication:** Not required.

Returns the details of the specified project.

**Success Response:** `200 OK`

```json
{
  "id": 5,
  "title": "Web Development Project",
  "description": "A project built with Django and React.",
  "creator": 1,
  "capacity": 4,
  "status": "open",
  "skills": [1, 2],
  "created_at": "2026-11-11T10:00:00Z",
  "updated_at": "2026-11-11T10:00:00Z"
}
```

## 4.4 Update Project

**Endpoint:** `PUT /api/projects/{id}/`

**Authentication:** Required.

**Permission:** Only the project creator can update the project.

The same permission rule applies to `PATCH`.

- `PUT`: Full update.
- `PATCH`: Partial update.

**Example PATCH Request:**

```json
{
  "title": "Updated Project Title"
}
```

**Success Response:** `200 OK`

Returns the updated project.

Requests from authenticated users who are not the project creator are denied.

## 4.5 Delete Project

**Endpoint:** `DELETE /api/projects/{id}/`

**Authentication:** Required.

**Permission:** Only the project creator can delete the project.

**Success Response:** `204 No Content`

Requests from users other than the creator are denied.

## 4.6 Get My Projects

**Endpoint:** `GET /api/projects/my/`

**Authentication:** Required.

Returns projects where the authenticated user is either:

- The project creator.
- A project member.

Each project includes an additional `role` field.

Possible values:

- `creator`
- `member`

**Example Response:**

```json
[
  {
    "id": 5,
    "title": "Web Development Project",
    "description": "A project built with Django and React.",
    "creator": 1,
    "capacity": 4,
    "status": "open",
    "skills": [1, 2],
    "created_at": "2026-11-11T10:00:00Z",
    "updated_at": "2026-11-11T10:00:00Z",
    "role": "creator"
  }
]
```

---

# 5. Project Response Structure

The standard Project response contains:

| Field | Description |
|---|---|
| `id` | Project ID |
| `title` | Project title |
| `description` | Project description |
| `creator` | ID of the project creator |
| `capacity` | Maximum number of members |
| `status` | `open` or `closed` |
| `skills` | List of Skill IDs |
| `created_at` | Creation timestamp |
| `updated_at` | Last update timestamp |

The `creator`, `id`, `created_at`, and `updated_at` fields are read-only.

---

# 6. HTTP Status Codes

| Status Code | Description |
|---|---|
| `200 OK` | Request successful |
| `201 Created` | Resource successfully created |
| `204 No Content` | Resource successfully deleted |
| `400 Bad Request` | Invalid request data |
| `401 Unauthorized` | Authentication required or invalid credentials |
| `403 Forbidden` | User does not have permission |
| `404 Not Found` | Resource not found |
| `405 Method Not Allowed` | HTTP method not supported |

---

# 7. Important Notes

- All authenticated requests must include the token in the `Authorization` header.
- Only the creator of a project can update or delete it.
- All users can retrieve project details.
- The project list endpoint returns only projects with `open` status.
- The `creator` field is assigned automatically when a project is created.
- Skills must refer to existing Skill IDs.

## 8. Not Yet Implemented

The following APIs are not currently implemented:

- Skills list/retrieval endpoint.
- Membership request endpoints.

These endpoints should not be used by the frontend until they are implemented and documented.