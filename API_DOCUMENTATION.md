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

## 3.5 Google Authentication (Login & Signup)

### 3.5.1 Google OAuth Verify & Exchange

**Endpoint:** `POST /api/users/google/`

**Authentication:** Not required.

Seamlessly authenticates existing users or provisions new accounts via Google. Accepts a Google ID token, OAuth2 access token, or authorization code.

**Request Body (ID Token - Recommended for SPA):**

```json
{
  "id_token": "YOUR_GOOGLE_ID_TOKEN"
}
```

**Alternative Request Bodies:**

```json
{
  "access_token": "YOUR_GOOGLE_ACCESS_TOKEN"
}
```

or:

```json
{
  "code": "YOUR_GOOGLE_AUTH_CODE",
  "redirect_uri": "http://localhost:5173/auth/callback"
}
```

**Success Response:** `200 OK`

```json
{
  "token": "YOUR_AUTH_TOKEN",
  "user": {
    "id": 1,
    "email": "user@example.com",
    "username": "user_name"
  },
  "is_new_user": false
}
```

- If the user email does not exist, a new user account is automatically registered (`is_new_user: true`) with an auto-generated unique username and unusable password.
- If the user already exists, they are authenticated directly (`is_new_user: false`).

**Error Response:** `400 Bad Request`

```json
{
  "detail": "Invalid or expired Google ID token."
}
```

### 3.5.2 Google Login Redirect

**Endpoint:** `GET /api/users/google/login/`

**Authentication:** Not required.

Generates the Google OAuth 2.0 consent page URL.

- Calling from a browser redirects (302) to Google's sign-in screen.
- Calling with query `?format=json` returns `{"auth_url": "https://accounts.google.com/..."}`.

### 3.5.3 Google OAuth Callback

**Endpoint:** `GET /api/users/google/callback/`

**Authentication:** Not required.

Handles the redirect from Google with `?code=...` and forwards the user to the frontend with an authentication token:

`http://localhost:5173/login?token=YOUR_AUTH_TOKEN&email=user@example.com&username=user_name`

## 3.6 Password Reset Request

**Endpoint:** `POST /api/users/password-reset/`

**Authentication:** Not required.

Initiates a password reset request by sending a secure one-time reset link to the user's email address. To prevent account enumeration, this endpoint always returns `200 OK` regardless of whether the email address exists in the system.

**Request Body:**

```json
{
  "email": "user@example.com",
  "redirect_url": "http://localhost:5173/reset-password"
}
```

- `email` (Required): The email of the account to reset.
- `redirect_url` (Optional): Custom frontend URL where the user will be directed. If omitted, defaults to `${FRONTEND_URL}/reset-password`.

**Success Response:** `200 OK`

```json
{
  "message": "If an account with this email exists, a password reset link has been sent.",
  "status": "success"
}
```

**Email Sent to User:**
Contains a reset link formatted as:
`http://localhost:5173/reset-password?uid={uidb64}&token={token}`
Link is valid for 24 hours.

**Error Response:** `400 Bad Request` (e.g. invalid email format)

```json
{
  "email": ["Enter a valid email address."]
}
```

---

## 3.7 Password Reset Token Validation

**Endpoint:** `POST /api/users/password-reset/validate/` or `GET /api/users/password-reset/validate/?uid={uid}&token={token}`

**Authentication:** Not required.

Allows the frontend application to verify the validity and expiration of the reset token before displaying the new password input form to the user.

**Request Body (POST):**

```json
{
  "uid": "MQ",
  "token": "d7s12a-438902d8f92134e7f8"
}
```

**Success Response:** `200 OK`

```json
{
  "valid": true,
  "uid": "MQ",
  "username": "testuser",
  "message": "Token is valid."
}
```

**Error Response:** `400 Bad Request`

```json
{
  "valid": false,
  "message": "The password reset link is invalid or has expired."
}
```

---

## 3.8 Password Reset Confirm

**Endpoint:** `POST /api/users/password-reset/confirm/`

**Authentication:** Not required.

Applies the new password to the account using the verified token and UID. Upon success, any previous authentication tokens for the user are invalidated and a fresh token is issued.

**Request Body:**

```json
{
  "uid": "MQ",
  "token": "d7s12a-438902d8f92134e7f8",
  "new_password": "NewSecurePassword123",
  "confirm_password": "NewSecurePassword123"
}
```

**Success Response:** `200 OK`

```json
{
  "message": "Password has been successfully reset. You can now log in with your new password.",
  "token": "NEW_AUTH_TOKEN_KEY",
  "status": "success"
}
```

**Error Responses:**
- `400 Bad Request` (Token invalid or expired):
  ```json
  {
    "detail": "The password reset link is invalid or has expired."
  }
  ```
- `400 Bad Request` (Passwords do not match):
  ```json
  {
    "confirm_password": ["Passwords do not match."]
  }
  ```
- `400 Bad Request` (Password shorter than 8 characters):
  ```json
  {
    "new_password": ["Ensure this field has at least 8 characters."]
  }
  ```

---

## 3.9 Password Change (Authenticated)

**Endpoint:** `POST /api/users/password-change/`

**Authentication:** Required (`Token <token>`).

Allows an authenticated user to change their existing password by providing their current password and a new password.

**Request Body:**

```json
{
  "old_password": "CurrentPassword123",
  "new_password": "UpdatedPassword456",
  "confirm_password": "UpdatedPassword456"
}
```

**Success Response:** `200 OK`

```json
{
  "message": "Password changed successfully.",
  "status": "success"
}
```

**Error Responses:**
- `400 Bad Request` (Wrong current password):
  ```json
  {
    "old_password": ["Current password is incorrect."]
  }
  ```
- `400 Bad Request` (Confirmation mismatch):
  ```json
  {
    "confirm_password": ["Passwords do not match."]
  }
  ```
- `401 Unauthorized`: If the request lacks authentication.

---

## 3.10 API Health Check


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

Returns paginated requests relevant to the authenticated user (requests sent by the user as applicant, and requests received for projects owned by the user).

**Query Parameters:**
- `?project=1`: Filter requests for a specific project ID.
- `?status=pending`: Filter by status (`pending`, `accepted`, `rejected`).
- `?role=applicant`: Return only requests sent by the user.
- `?role=creator`: Return only requests received on user's projects.
- `?search=keyword`: Search by project title, applicant username, email, or message.
- `?ordering=-created_at`: Order by `created_at`, `status`, or `project__title`.
- `?page=1&page_size=10`: Pagination parameters.

**Success Response:** `200 OK`

```json
{
  "count": 1,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "project": 1,
      "project_title": "AI Skill Matcher Platform",
      "user": 2,
      "applicant_username": "applicant_user",
      "applicant_email": "applicant@example.com",
      "status": "pending",
      "message": "Hi, I have strong experience in Python...",
      "response_message": "",
      "created_at": "2026-11-23T10:00:00Z",
      "updated_at": "2026-11-23T10:00:00Z"
    }
  ]
}
```

## 5.3 Membership Request Analytics & Stats

**Endpoint:** `GET /api/applications/requests/stats/`

**Authentication:** Required.

Returns real-time metrics for the authenticated user, summarizing application statuses both as applicant and as project creator.

**Success Response:** `200 OK`

```json
{
  "sent": {
    "total": 5,
    "pending": 2,
    "accepted": 2,
    "rejected": 1
  },
  "received": {
    "total": 8,
    "pending": 3,
    "accepted": 4,
    "rejected": 1
  },
  "projects_to_review": [
    {
      "project_id": 1,
      "project_title": "AI Collaboration Platform",
      "pending_count": 3
    }
  ]
}
```

## 5.4 Get Membership Request Details

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
  "response_message": "Welcome to the team!",
  "created_at": "2026-11-23T10:00:00Z",
  "updated_at": "2026-11-23T10:00:00Z"
}
```

## 5.5 Accept or Reject Membership Request

**Endpoint:** `PATCH /api/applications/requests/{id}/`

**Authentication:** Required (Project Creator only).

Accepts or rejects a pending membership request, with an optional response message/feedback to the applicant.

**Request Body (Accept):**

```json
{
  "status": "accepted",
  "response_message": "Welcome to our engineering team!"
}
```

**Request Body (Reject):**

```json
{
  "status": "rejected",
  "response_message": "Thank you for applying. We are currently looking for a senior contributor."
}
```

**Behavior on Accept:**
- Transactional operation (`transaction.atomic`) with database row locking (`select_for_update`).
- Automatically adds the applicant to `ProjectMember`.
- Decrements project remaining capacity.
- Automatically closes the project (`status = 'closed'`) if capacity reaches full.

**Success Response:** `200 OK`

```json
{
  "status": "accepted",
  "response_message": "Welcome to our engineering team!"
}
```

**Validation & Error Responses:**
- `400 Bad Request`: If status is not `accepted` or `rejected`, or if request is already finalized, or if capacity is full.
- `403 Forbidden`: If user is not the project creator.

## 5.6 Withdraw Membership Request

**Endpoint:** `DELETE /api/applications/requests/{id}/`

**Authentication:** Required (Applicant only).

Allows an applicant to cancel and delete their own pending request.

**Success Response:** `204 No Content`

**Error Responses:**
- `400 Bad Request`: If request has already been accepted or rejected.
- `403 Forbidden`: If requesting user is not the applicant.

## 5.7 Project Members List

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

## 5.8 Remove Project Member or Leave Team

**Endpoint:** `DELETE /api/projects/{id}/members/{user_id}/`

**Authentication:** Required.

Allows a project creator to remove an accepted member from their team, or allows a member to voluntarily leave the project.

- If the project was previously closed due to full capacity, removing a member automatically re-opens the project (`status = 'open'`).

**Success Response:** `204 No Content`

**Error Responses:**
- `403 Forbidden`: If the user is neither the project creator nor the member themselves.
- `404 Not Found`: If the project or member does not exist.

