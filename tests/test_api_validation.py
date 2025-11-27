"""
Test API Input Validation.

Tests for request validation, error handling, and edge cases.
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_shorten_url_success(test_client: AsyncClient, sample_urls):
    """Test successful URL shortening via API."""
    response = await test_client.post(
        "/api/v1/urls/shorten",
        json={"original_url": sample_urls[0]}
    )
    
    assert response.status_code == 201
    data = response.json()
    
    assert "short_code" in data
    assert "short_url" in data
    assert "original_url" in data
    assert "created_at" in data
    assert len(data["short_code"]) == 5


@pytest.mark.asyncio
async def test_shorten_url_invalid_format(test_client: AsyncClient):
    """Test that invalid URL format returns 400."""
    response = await test_client.post(
        "/api/v1/urls/shorten",
        json={"original_url": "not-a-valid-url"}
    )
    
    assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_shorten_url_missing_field(test_client: AsyncClient):
    """Test that missing original_url field returns 422."""
    response = await test_client.post(
        "/api/v1/urls/shorten",
        json={}
    )
    
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_shorten_url_empty_string(test_client: AsyncClient):
    """Test that empty URL string returns error."""
    response = await test_client.post(
        "/api/v1/urls/shorten",
        json={"original_url": ""}
    )
    
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_shorten_url_malicious_url(test_client: AsyncClient):
    """Test that malicious URLs are rejected."""
    malicious_urls = [
        "http://localhost/admin",
        "http://127.0.0.1/internal",
        "http://192.168.1.1/router",
    ]
    
    for url in malicious_urls:
        response = await test_client.post(
            "/api/v1/urls/shorten",
            json={"original_url": url}
        )
        assert response.status_code in [400, 422]


@pytest.mark.asyncio
async def test_get_url_stats_success(test_client: AsyncClient, sample_urls):
    """Test getting URL statistics."""
    # First create a short URL
    create_response = await test_client.post(
        "/api/v1/urls/shorten",
        json={"original_url": sample_urls[0]}
    )
    assert create_response.status_code == 201
    short_code = create_response.json()["short_code"]
    
    # Get stats
    stats_response = await test_client.get(f"/api/v1/urls/{short_code}/stats")
    assert stats_response.status_code == 200
    
    data = stats_response.json()
    assert data["short_code"] == short_code
    assert data["original_url"] == sample_urls[0]
    assert data["click_count"] >= 0
    assert "created_at" in data


@pytest.mark.asyncio
async def test_get_url_stats_not_found(test_client: AsyncClient):
    """Test getting stats for non-existent short code."""
    response = await test_client.get("/api/v1/urls/XXXXX/stats")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_health_check(test_client: AsyncClient):
    """Test health check endpoint."""
    response = await test_client.get("/api/v1/health")
    assert response.status_code == 200
    
    data = response.json()
    assert "status" in data
    assert "database" in data
    assert "redis" in data
    assert "timestamp" in data


@pytest.mark.asyncio
async def test_redirect_endpoint(test_client: AsyncClient, sample_urls):
    """Test redirect endpoint."""
    # Create short URL
    create_response = await test_client.post(
        "/api/v1/urls/shorten",
        json={"original_url": sample_urls[0]}
    )
    short_code = create_response.json()["short_code"]
    
    # Access redirect endpoint (follow_redirects=False to check redirect)
    redirect_response = await test_client.get(
        f"/{short_code}",
        follow_redirects=False
    )
    
    assert redirect_response.status_code == 307
    assert redirect_response.headers["location"] == sample_urls[0]


@pytest.mark.asyncio
async def test_redirect_not_found(test_client: AsyncClient):
    """Test redirect with non-existent short code."""
    response = await test_client.get("/XXXXX", follow_redirects=False)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_maximum_url_length(test_client: AsyncClient):
    """Test that very long URLs are handled appropriately."""
    # Create a URL that exceeds maximum length
    long_url = "https://example.com/" + "a" * 3000
    
    response = await test_client.post(
        "/api/v1/urls/shorten",
        json={"original_url": long_url}
    )
    
    # Should be rejected with validation error or bad request
    assert response.status_code in [400, 422]

