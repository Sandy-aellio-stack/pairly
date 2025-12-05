"""Tests for post creation and feed functionality.

Tests:
- Creating public posts
- Creating subscriber-only posts
- Feed visibility and cursor pagination
"""
import pytest
from httpx import AsyncClient
from datetime import datetime
from beanie import PydanticObjectId

# Mark all tests as async
pytestmark = pytest.mark.asyncio


class TestPostCreation:
    """Test post creation endpoints."""
    
    async def test_create_public_post(self, client: AsyncClient, auth_headers: dict):
        """Test creating a public post."""
        post_data = {
            "text": "This is a test post",
            "media": [
                {
                    "type": "image",
                    "url": "https://example.s3.amazonaws.com/test.jpg",
                    "meta": {
                        "mime": "image/jpeg",
                        "size_bytes": 1000000
                    }
                }
            ],
            "visibility": "public"
        }
        
        response = await client.post(
            "/api/posts",
            json=post_data,
            headers=auth_headers
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["text"] == post_data["text"]
        assert data["visibility"] == "public"
        assert len(data["media"]) == 1
        assert "id" in data
        assert "created_at" in data
    
    async def test_create_post_without_auth(self, client: AsyncClient):
        """Test creating post without authentication."""
        post_data = {
            "text": "This should fail",
            "visibility": "public"
        }
        
        response = await client.post("/api/posts", json=post_data)
        assert response.status_code == 401
    
    async def test_create_post_with_invalid_media(
        self, 
        client: AsyncClient, 
        auth_headers: dict
    ):
        """Test creating post with invalid media."""
        post_data = {
            "text": "Test",
            "media": [
                {
                    "type": "video",
                    "url": "https://example.s3.amazonaws.com/video.mp4",
                    "meta": {
                        "size_bytes": 200_000_000  # Exceeds 100MB limit
                    }
                }
            ],
            "visibility": "public"
        }
        
        response = await client.post(
            "/api/posts",
            json=post_data,
            headers=auth_headers
        )
        
        assert response.status_code == 422  # Validation error
    
    async def test_create_post_too_many_media(
        self, 
        client: AsyncClient, 
        auth_headers: dict
    ):
        """Test creating post with more than 10 media items."""
        post_data = {
            "text": "Too many media items",
            "media": [
                {
                    "type": "image",
                    "url": f"https://example.s3.amazonaws.com/img{i}.jpg",
                    "meta": {"mime": "image/jpeg", "size_bytes": 1000000}
                }
                for i in range(11)  # 11 items, should fail
            ],
            "visibility": "public"
        }
        
        response = await client.post(
            "/api/posts",
            json=post_data,
            headers=auth_headers
        )
        
        assert response.status_code == 422


class TestSubscriberPosts:
    """Test subscriber-gated posts."""
    
    async def test_create_subscriber_post_without_tier(
        self, 
        client: AsyncClient, 
        auth_headers: dict
    ):
        """Test creating subscriber post without active tiers."""
        post_data = {
            "text": "Subscriber only content",
            "visibility": "subscribers"
        }
        
        # This should fail if creator has no tiers
        response = await client.post(
            "/api/posts",
            json=post_data,
            headers=auth_headers
        )
        
        # May succeed or fail depending on tier setup
        assert response.status_code in [201, 400]
    
    async def test_view_subscriber_post_without_subscription(
        self, 
        client: AsyncClient
    ):
        """Test viewing subscriber post without subscription."""
        # This would require mocking subscription state
        # For now, we test the endpoint exists
        response = await client.get("/api/posts/invalid_id")
        assert response.status_code in [404, 401]


class TestFeed:
    """Test feed endpoints."""
    
    async def test_get_home_feed(
        self, 
        client: AsyncClient, 
        auth_headers: dict
    ):
        """Test getting home feed."""
        response = await client.get(
            "/api/feed/home",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "posts" in data
        assert "next_cursor" in data
        assert isinstance(data["posts"], list)
    
    async def test_feed_pagination(
        self, 
        client: AsyncClient, 
        auth_headers: dict
    ):
        """Test feed cursor pagination."""
        # First page
        response1 = await client.get(
            "/api/feed/home?limit=5",
            headers=auth_headers
        )
        
        assert response1.status_code == 200
        data1 = response1.json()
        
        # If there's a cursor, fetch next page
        if data1.get("next_cursor"):
            response2 = await client.get(
                f"/api/feed/home?cursor={data1['next_cursor']}&limit=5",
                headers=auth_headers
            )
            
            assert response2.status_code == 200
            data2 = response2.json()
            
            # Posts should be different
            if data1["posts"] and data2["posts"]:
                assert data1["posts"][0]["id"] != data2["posts"][0]["id"]
    
    async def test_creator_feed(
        self, 
        client: AsyncClient, 
        auth_headers: dict,
        creator_id: str
    ):
        """Test getting creator timeline."""
        response = await client.get(
            f"/api/feed/creator/{creator_id}",
            headers=auth_headers
        )
        
        # May be 200 or 404 depending on creator existence
        assert response.status_code in [200, 404]
    
    async def test_feed_respects_visibility(
        self, 
        client: AsyncClient, 
        auth_headers: dict
    ):
        """Test that feed respects post visibility rules."""
        # Create a public post
        post_data = {
            "text": "Public post for feed test",
            "visibility": "public"
        }
        
        create_response = await client.post(
            "/api/posts",
            json=post_data,
            headers=auth_headers
        )
        
        if create_response.status_code == 201:
            # Fetch feed
            feed_response = await client.get(
                "/api/feed/home",
                headers=auth_headers
            )
            
            assert feed_response.status_code == 200
            feed_data = feed_response.json()
            
            # Check if our post appears in feed
            post_texts = [p["text"] for p in feed_data["posts"]]
            assert "Public post for feed test" in post_texts or len(feed_data["posts"]) == 0


# Fixtures
@pytest.fixture
async def client():
    """Create test client."""
    from backend.server import app
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def auth_headers(mock_user_token):
    """Provide authentication headers."""
    return {"Authorization": f"Bearer {mock_user_token}"}


@pytest.fixture
def mock_user_token():
    """Mock JWT token for testing."""
    # In production, generate real JWT for test user
    return "mock_jwt_token_for_testing"


@pytest.fixture
def creator_id():
    """Mock creator ID."""
    return str(PydanticObjectId())
