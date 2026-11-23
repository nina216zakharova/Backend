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
  "skills"
}
```

## 4.4 Explore Projects API

**Endpoint:** `/api/projects/explore/`

**Method:** `GET`

**Description:**

Returns projects for the Explore Projects page. Supports searching, filtering by project status and required skills, and ordering projects by creation date.

**Authentication:** Not required (Public endpoint).

#### Query Parameters

| Parameter | Description | Accepted Values | Default |
|---|---|---|---|
| `search` | Search by project title and description | Keyword | None |
| `status` | Filter projects by status | `open`, `closed` | `open` |
| `skill` | Filter by required skill ID | Skill ID (integer) | None |
| `ordering` | Sort projects by creation date | `created_at`, `-created_at` | `-created_at` |

#### Examples

**1. Get all open projects (default):**
```http
GET /api/projects/explore/
```

**2. Get closed projects:**
```http
GET /api/projects/explore/?status=closed
```

**3. Get newest projects:**
```http
GET /api/projects/explore/?ordering=-created_at
```

**4. Get oldest projects:**
```http
GET /api/projects/explore/?ordering=created_at
```

**5. Search projects:**
```http
GET /api/projects/explore/?search=Python
```

**6. Filter projects by skill:**
```http
GET /api/projects/explore/?skill=2
```

**7. Combine multiple filters:**
```http
GET /api/projects/explore/?status=open&skill=2&ordering=-created_at&search=Python
```

#### Validation

- If no `status` parameter is provided, only open projects are returned.
- The `status` parameter accepts only `open` or `closed`.
- Invalid status values return `400 Bad Request`.
- Projects are ordered by newest first by default.
- Multiple query parameters can be combined in a single request.

#### Response

Returns a list of projects using `ProjectSerializer`.

Each project contains:
- `id`
- `title`
- `goal`
- `description`
- `creator`
- `capacity`
- `remaining_capacity`
- `status`
- `skills`
- `created_at`
- `updated_at`

---

# 5. Membership Request APIs

## 5.1 Submit Membership Request

**Endpoint:** `POST /api/applications/requests/`

**Authentication:** Required.

Submits a membership request to join a project.

**Request Body:**

```json
{
  "project": 1,
  "message": "Hi, I have strong experience in Python and would love to collaborate."
}
```

Fields:
- `project`: Required. ID of the target project.
- `message`: Optional. Application note or message to the project creator.

**Success Response:** `201 Created`

```json
{
  "id": 1,
  "project": 1,
  "message": "Hi, I have strong experience in Python and would love to collaborate.",
  "status": "pending",
  "applicant_username": "applicant_user",
  "created_at": "2026-11-23T10:00:00Z"
}
```

**Validation & Error Responses:** `400 Bad Request`
- Target project must be open (`status == 'open'`).
- Creators cannot apply to their own projects.
- Existing project members cannot apply again.
- Duplicate pending requests are rejected.
- Projects with full capacity reject new requests.

## 5.2 List Membership Requests

**Endpoint:** `GET /api/applications/requests/`

**Authentication:** Required.

Returns requests relevant to the authenticated user (requests sent by the user as applicant, and requests received for projects owned by the user).

**Optional Query Parameters:**
- `?project=1`: Filter requests for a specific project.
- `?status=pending`: Filter by status (`pending`, `accepted`, `rejected`).
- `?role=applicant`: Return only requests sent by the user.
- `?role=creator`: Return only requests received on user's projects.

**Success Response:** `200 OK`

```json
[
  {
    "id": 1,
    "project": 1,
    "project_title": "AI Skill Matcher Platform",
    "user": 2,
    "applicant_username": "applicant_user",
    "applicant_email": "applicant@example.com",
    "status": "pending",
    "message": "Hi, I have strong experience in Python...",
    "created_at": "2026-11-23T10:00:00Z",
    "updated_at": "2026-11-23T10:00:00Z"
  }
]
```

## 5.3 Get Membership Request Details

**Endpoint:** `GET /api/applications/requests/{id}/`

**Authentication:** Required (Applicant or Project Creator).

**Success Response:** `200 OK`

```json
{
  "id": 1,
  "project": 1,
  "project_title": "AI Skill Matcher Platform",
  "user": 2,
  "applicant_username": "applicant_user",
  "applicant_email": "applicant@example.com",
  "status": "pending",
  "message": "Hi, I have strong experience in Python...",
  "created_at": "2026-11-23T10:00:00Z",
  "updated_at": "2026-11-23T10:00:00Z"
}
```

## 5.4 Accept or Reject Membership Request

**Endpoint:** `PATCH /api/applications/requests/{id}/`

**Authentication:** Required (Project Creator only).

Accepts or rejects a pending membership request.

**Request Body (Accept):**

```json
{
  "status": "accepted"
}
```

**Request Body (Reject):**

```json
{
  "status": "rejected"
}
```

**Behavior on Accept:**
- Transactional operation (`transaction.atomic`).
- Automatically adds the applicant to `ProjectMember`.
- Decrements project remaining capacity.
- Automatically closes the project (`status = 'closed'`) if capacity reaches full.

**Success Response:** `200 OK`

```json
{
  "status": "accepted"
}
```

**Validation & Error Responses:**
- `400 Bad Request`: If status is not `accepted` or `rejected`, or if request is already finalized, or if capacity is full.
- `403 Forbidden`: If user is not the project creator.

## 5.5 Withdraw Membership Request

**Endpoint:** `DELETE /api/applications/requests/{id}/`

**Authentication:** Required (Applicant only).

Allows an applicant to cancel and delete their own pending request.

**Success Response:** `204 No Content`

**Error Responses:**
- `400 Bad Request`: If request has already been accepted or rejected.
- `403 Forbidden`: If requesting user is not the applicant.

## 5.6 Project Members List

**Endpoint:** `GET /api/projects/{id}/members/`

**Authentication:** Optional.

Returns all accepted team members for a given project.

**Success Response:** `200 OK`

```json
[
  {
    "id": 1,
    "user": {
      "id": 2,
      "username": "applicant_user",
      "email": "applicant@example.com"
    },
    "joined_at": "2026-11-23T10:15:00Z"
  }
]
```
