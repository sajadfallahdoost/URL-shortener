# API Documentation

Complete API reference for the URL Shortener service.

## Base URL

```
http://localhost:8000/api/v1
```

## Authentication

Currently, no authentication is required. Rate limiting is applied per IP address.

---

## Endpoints

### 1. Health Check

Check the health status of the application and its dependencies.

**Endpoint:** `GET /health`

**Response:** `200 OK`

```json
{
  "status": "healthy",
  "database": "connected",
  "redis": "connected",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

**Status Values:**
- `healthy`: All services operational
- `unhealthy`: One or more services down

---

### 2. Shorten URL

Create a shortened URL from a long URL.

**Endpoint:** `POST /urls/shorten`

**Request Body:**

```json
{
  "original_url": "https://www.example.com/very/long/path/to/page"
}
```

**Response:** `201 Created`

```json
{
  "short_code": "aB3xY",
  "short_url": "http://localhost:8000/aB3xY",
  "original_url": "https://www.example.com/very/long/path/to/page",
  "created_at": "2024-01-15T10:30:00Z"
}
```

**Field Descriptions:**
- `short_code`: 5-character unique identifier
- `short_url`: Complete shortened URL
- `original_url`: The original long URL
- `created_at`: ISO 8601 timestamp of creation

**Validation Rules:**
- URL must be valid HTTP/HTTPS
- Maximum URL length: 2048 characters
- Localhost and private networks are blocked
- If URL already exists, returns existing short code

**Error Responses:**

```json
// 400 Bad Request - Invalid URL
{
  "error": "Invalid URL format",
  "details": {
    "url": "not-a-url",
    "reason": "Invalid URL format"
  }
}

// 422 Unprocessable Entity - Validation error
{
  "error": "Validation error",
  "details": [
    {
      "loc": ["body", "original_url"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}

// 500 Internal Server Error - Server error
{
  "error": "Unable to generate unique short code. Please try again.",
  "details": null
}
```

**Example:**

```bash
curl -X POST "http://localhost:8000/api/v1/urls/shorten" \
  -H "Content-Type: application/json" \
  -d '{
    "original_url": "https://github.com/user/repo/issues/123"
  }'
```

---

### 3. Get URL Statistics

Retrieve statistics for a shortened URL.

**Endpoint:** `GET /urls/{short_code}/stats`

**Path Parameters:**
- `short_code` (string, required): The 5-character short code

**Response:** `200 OK`

```json
{
  "short_code": "aB3xY",
  "original_url": "https://www.example.com/very/long/path/to/page",
  "click_count": 42,
  "created_at": "2024-01-15T10:30:00Z",
  "last_accessed_at": "2024-01-15T14:20:00Z"
}
```

**Field Descriptions:**
- `click_count`: Number of times the short URL was accessed
- `last_accessed_at`: Last redirect timestamp (null if never accessed)

**Error Response:**

```json
// 404 Not Found
{
  "error": "URL with short code 'XXXXX' not found",
  "details": {
    "short_code": "XXXXX"
  }
}
```

**Example:**

```bash
curl "http://localhost:8000/api/v1/urls/aB3xY/stats"
```

---

### 4. Redirect to Original URL

Redirect from short code to original URL.

**Endpoint:** `GET /{short_code}`

**Path Parameters:**
- `short_code` (string, required): The 5-character short code

**Response:** `307 Temporary Redirect`

**Headers:**
```
Location: https://www.example.com/very/long/path/to/page
```

**Behavior:**
- Returns 307 redirect with Location header
- Increments click_count for the URL
- Updates last_accessed_at timestamp
- Cached in Redis for fast subsequent access

**Error Response:**

```json
// 404 Not Found
{
  "error": "Short code 'XXXXX' not found"
}
```

**Example:**

```bash
# Without following redirect
curl -i "http://localhost:8000/aB3xY"

# Following redirect
curl -L "http://localhost:8000/aB3xY"
```

---

## Rate Limiting

**Limits:**
- 100 requests per minute per IP address
- Applies to all endpoints

**Rate Limit Headers:**
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 99
X-RateLimit-Reset: 1642242000
```

**Rate Limit Exceeded Response:** `429 Too Many Requests`

```json
{
  "error": "Rate limit exceeded: 100 requests per minute",
  "details": {
    "limit": 100,
    "window": "minute"
  }
}
```

---

## Error Codes

| Status Code | Description |
|-------------|-------------|
| 200 | Success |
| 201 | Created |
| 307 | Temporary Redirect |
| 400 | Bad Request - Invalid input |
| 404 | Not Found - Resource doesn't exist |
| 422 | Unprocessable Entity - Validation error |
| 429 | Too Many Requests - Rate limit exceeded |
| 500 | Internal Server Error |

---

## CORS

CORS is configured to allow requests from specified origins.

**Default Allowed Origins:**
- `http://localhost:3000`
- `http://localhost:8000`

Configure via `CORS_ORIGINS` environment variable (comma-separated).

---

## Interactive Documentation

**Swagger UI:** http://localhost:8000/api/docs  
**ReDoc:** http://localhost:8000/api/redoc

Both provide interactive API exploration and testing capabilities.

---

## Code Examples

### Python

```python
import requests

# Shorten URL
response = requests.post(
    "http://localhost:8000/api/v1/urls/shorten",
    json={"original_url": "https://example.com/long/path"}
)
data = response.json()
print(f"Short URL: {data['short_url']}")

# Get stats
stats = requests.get(
    f"http://localhost:8000/api/v1/urls/{data['short_code']}/stats"
).json()
print(f"Clicks: {stats['click_count']}")
```

### JavaScript

```javascript
// Shorten URL
const response = await fetch('http://localhost:8000/api/v1/urls/shorten', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({
    original_url: 'https://example.com/long/path'
  })
});
const data = await response.json();
console.log('Short URL:', data.short_url);

// Get stats
const stats = await fetch(
  `http://localhost:8000/api/v1/urls/${data.short_code}/stats`
).then(r => r.json());
console.log('Clicks:', stats.click_count);
```

### cURL

```bash
# Shorten URL
SHORT_CODE=$(curl -s -X POST "http://localhost:8000/api/v1/urls/shorten" \
  -H "Content-Type: application/json" \
  -d '{"original_url": "https://example.com/long/path"}' \
  | jq -r '.short_code')

# Use short URL
curl -L "http://localhost:8000/$SHORT_CODE"

# Get stats
curl "http://localhost:8000/api/v1/urls/$SHORT_CODE/stats" | jq
```

---

## Webhooks & Events

Currently not supported. This is a planned feature for future releases.

---

## Versioning

The API uses URL-based versioning (`/api/v1/`).

**Current Version:** v1  
**Status:** Stable

Breaking changes will be introduced in new versions (v2, v3, etc.).

