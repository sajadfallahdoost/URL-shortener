# Architecture Documentation

System design, technology choices, and scaling strategy for the URL Shortener service.

## Table of Contents

1. [High-Level Architecture](#high-level-architecture)
2. [Technology Stack](#technology-stack)
3. [Database Schema](#database-schema)
4. [Caching Strategy](#caching-strategy)
5. [URL Shortening Algorithm](#url-shortening-algorithm)
6. [Scaling Strategy](#scaling-strategy)
7. [Performance Considerations](#performance-considerations)

---

## High-Level Architecture

### System Components

```
                    ┌───────────────┐
                    │   Internet    │
                    └───────┬───────┘
                            │
                    ┌───────▼────────┐
                    │  Load Balancer │  (Optional)
                    │    (Nginx)     │
                    └───────┬────────┘
                            │
         ┌──────────────────┼──────────────────┐
         │                  │                  │
    ┌────▼────┐       ┌─────▼─────┐     ┌─────▼─────┐
    │FastAPI  │       │  FastAPI  │     │  FastAPI  │
    │Instance │       │ Instance  │     │ Instance  │
    │   #1    │       │    #2     │     │    #3     │
    └────┬────┘       └─────┬─────┘     └─────┬─────┘
         │                  │                  │
         └──────────────────┼──────────────────┘
                            │
                    ┌───────▼────────┐
                    │  Redis Cluster │
                    │    (Cache)     │
                    └───────┬────────┘
                            │
                    ┌───────▼────────┐
                    │   PostgreSQL   │
                    │   (Primary)    │
                    └────────────────┘
                            │
              ┌─────────────┴─────────────┐
              │                           │
        ┌─────▼──────┐            ┌──────▼─────┐
        │ PostgreSQL │            │ PostgreSQL │
        │   Replica  │            │   Replica  │
        │    (RO)    │            │    (RO)    │
        └────────────┘            └────────────┘
```

### Layer Architecture

```
┌─────────────────────────────────────────┐
│          Presentation Layer             │
│  • FastAPI Endpoints                    │
│  • Request/Response Validation          │
│  • Rate Limiting Middleware             │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│          Business Logic Layer           │
│  • URL Service                          │
│  • Short Code Generator                 │
│  • URL Validator                        │
│  • Caching Logic                        │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│        Data Access Layer (DAL)          │
│  • URL Repository                       │
│  • Database Queries                     │
│  • Transaction Management               │
└─────────────────┬───────────────────────┘
                  │
         ┌────────┴────────┐
         │                 │
    ┌────▼────┐      ┌────▼────┐
    │Database │      │  Cache  │
    │(Postgres)      │ (Redis) │
    └─────────┘      └─────────┘
```

---

## Technology Stack

### Backend Framework

**FastAPI** - Modern Python web framework
- **Why**: Async support, automatic OpenAPI docs, Pydantic validation
- **Pros**: High performance, type safety, developer experience
- **Cons**: Relatively new ecosystem

### Database

**PostgreSQL 15** - Relational database
- **Why**: ACID compliance, reliability, mature ecosystem
- **Usage**: Primary data store for URL mappings
- **Features Used**: 
  - Unique constraints for deduplication
  - Indexes for fast lookups
  - Timestamp support with timezone

### Cache

**Redis 7** - In-memory data store
- **Why**: Sub-millisecond latency, pub/sub support (future)
- **Usage**: Caching URL mappings for fast redirects
- **TTL**: 24 hours (configurable)
- **Reduces DB load**: 80%+

### ORM

**SQLAlchemy 2.0** - Python SQL toolkit
- **Why**: Async support, migration support, type safety
- **Usage**: Database abstraction and async queries
- **Features**: Connection pooling, session management

### Migration Tool

**Alembic** - Database migration tool
- **Why**: Standard for SQLAlchemy, version control for schema
- **Usage**: Managing database schema changes

---

## Database Schema

Based on `docs/database/database-design.dbml`:

### URLs Table

```sql
CREATE TABLE urls (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    original_url    TEXT NOT NULL UNIQUE,
    short_code      VARCHAR(5) NOT NULL UNIQUE,
    created_at      TIMESTAMP NOT NULL DEFAULT NOW(),
    click_count     BIGINT NOT NULL DEFAULT 0,
    last_accessed_at TIMESTAMP NULL
);

-- Indexes
CREATE UNIQUE INDEX idx_short_code ON urls(short_code);
CREATE UNIQUE INDEX idx_original_url ON urls(original_url);
CREATE INDEX idx_short_code_created ON urls(short_code, created_at);
CREATE INDEX idx_created_clicks ON urls(created_at, click_count);
```

### Design Decisions

1. **Unique Constraint on original_url**: Prevents duplicate URLs
2. **VARCHAR(5) for short_code**: Fixed length for Base62 codes
3. **BigInt for click_count**: Supports billions of clicks
4. **Composite Indexes**: Optimizes analytics queries

### Storage Estimates

- **Average row size**: ~200 bytes
- **1M URLs**: ~200 MB
- **10M URLs**: ~2 GB
- **100M URLs**: ~20 GB

---

## Caching Strategy

### Read-Through Cache Pattern

```
GET /{short_code}
    │
    ├─→ Check Redis Cache
    │   ├─→ Hit: Return URL (< 5ms)
    │   │   └─→ Increment click count (async)
    │   │
    │   └─→ Miss: Query Database
    │       ├─→ Found: Cache it, return URL (< 50ms)
    │       └─→ Not Found: Return 404
```

### Cache Keys

Pattern: `url:short:{short_code}`

Example: `url:short:aB3xY`

### Cache Configuration

- **TTL**: 24 hours (86,400 seconds)
- **Eviction Policy**: LRU (Least Recently Used)
- **Max Memory**: Configurable (default: 2GB)

### Cache Hit Ratio

Expected: 80-90% for production workloads

**Benefits:**
- Reduced database load
- Faster response times
- Better scalability

---

## URL Shortening Algorithm

### Base62 Encoding

**Character Set**: `a-z, A-Z, 0-9` (62 characters)

**Formula**: 62^5 = 916,132,832 possible combinations

### Generation Strategy

**Random Generation** (Current Implementation)

```python
def generate_short_code():
    # Generate random 5-char code from Base62
    code = random.choices(BASE62_CHARS, k=5)
    
    # Check for collision
    while check_exists(code):
        code = random.choices(BASE62_CHARS, k=5)
    
    return code
```

**Pros:**
- Simple implementation
- Difficult to predict next code
- Even distribution

**Cons:**
- Collision checks required
- Slightly slower than sequential

### Alternative: Sequential ID Encoding

```python
def encode_id(id: int) -> str:
    # Convert integer ID to Base62
    # Example: 12345 -> "3D7"
    result = []
    while id > 0:
        id, remainder = divmod(id, 62)
        result.append(BASE62_CHARS[remainder])
    return ''.join(reversed(result))
```

**Pros:**
- No collision checks
- Faster generation
- Predictable

**Cons:**
- Sequential codes (security concern)
- Leaks total URL count

---

## Scaling Strategy

### Vertical Scaling

**Current Setup** (Single Instance):
- 4 CPU cores
- 8GB RAM
- Expected: 10,000 req/s

### Horizontal Scaling

**Multiple App Instances:**

```
┌──────────────────┐
│  Load Balancer   │
└────────┬─────────┘
         │
    ┌────┼────┐
    │    │    │
┌───▼┐ ┌─▼─┐ ┌▼───┐
│App1│ │App2 │App3│
└────┘ └───┘ └────┘
```

**Configuration:**
- Session-less (stateless)
- Shared Redis and PostgreSQL
- Nginx load balancer

**Expected Capacity:**
- 3 instances: 30,000 req/s
- 10 instances: 100,000 req/s

### Database Scaling

**Read Replicas:**

```
       ┌─────────┐
       │ Primary │ (Writes)
       └────┬────┘
            │
    ┌───────┼───────┐
    │       │       │
┌───▼┐  ┌───▼┐  ┌──▼─┐
│Rep1│  │Rep2│  │Rep3│ (Reads)
└────┘  └────┘  └────┘
```

**Usage:**
- Primary: Write operations (create URL)
- Replicas: Read operations (stats, lookups)

### Redis Scaling

**Redis Cluster** (for high traffic):

```
┌───────┐  ┌───────┐  ┌───────┐
│Redis 1│  │Redis 2│  │Redis 3│
│Master │  │Master │  │Master │
└───┬───┘  └───┬───┘  └───┬───┘
    │          │          │
┌───▼───┐  ┌───▼───┐  ┌───▼───┐
│Replica│  │Replica│  │Replica│
└───────┘  └───────┘  └───────┘
```

**Benefits:**
- Higher throughput
- Automatic sharding
- High availability

---

## Performance Considerations

### Bottlenecks

1. **Database Queries**: Mitigated by caching
2. **Code Generation**: Optimized with efficient algorithm
3. **Network Latency**: Use CDN for global distribution

### Optimizations

1. **Connection Pooling**: Reuse database connections
2. **Async I/O**: Non-blocking operations
3. **Indexing**: Fast database lookups
4. **Caching**: Redis for hot data

### Monitoring Metrics

- Request latency (p50, p95, p99)
- Cache hit ratio
- Database query time
- Error rate
- Throughput (req/s)

### Expected Performance

| Metric | Target |
|--------|--------|
| Redirect (cache hit) | < 5ms |
| Redirect (cache miss) | < 50ms |
| URL Creation | < 100ms |
| Uptime | 99.9% |
| Cache Hit Ratio | > 80% |

---

## Security Considerations

### SSRF Protection

Block localhost and private networks:
- `localhost`, `127.0.0.1`
- `10.0.0.0/8`
- `172.16.0.0/12`
- `192.168.0.0/16`

### Rate Limiting

- 100 requests/minute per IP
- Prevents abuse and DDoS

### Input Validation

- URL format validation
- Length limits (max 2048 chars)
- Protocol validation (HTTP/HTTPS only)

---

## Future Enhancements

1. **Custom Short Codes**: User-defined codes
2. **Expiration**: TTL for URLs
3. **Authentication**: API keys for tracking
4. **Analytics Dashboard**: Visualize statistics
5. **QR Code Generation**: Generate QR codes
6. **Webhooks**: Event notifications

