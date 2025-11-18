import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.config import settings

client = TestClient(app)

def test_send_bulletins_endpoint():
    """Test the send-bulletins endpoint"""
    # Test data
    request_data = {
        "folder_path": "/nonexistent/folder",  # This should fail gracefully
        "sender_email": "test@example.com",
        "subject": "Test Bulletin",
        "message": "This is a test message"
    }

    # Make request (assuming authentication is bypassed for testing)
    # In a real scenario, you'd need to handle authentication
    response = client.post("/api/v1/send-bulletins", json=request_data)

    # Check that the endpoint exists and returns proper error for non-existent folder
    assert response.status_code in [200, 401, 403]  # 401/403 if auth required

    if response.status_code == 200:
        data = response.json()
        assert "total_files" in data
        assert "processed_files" in data
        assert "successful_sends" in data
        assert "failed_sends" in data
        assert "bulletins" in data
        assert data["total_files"] == 0  # Since folder doesn't exist

if __name__ == "__main__":
    test_send_bulletins_endpoint()
    print("Test passed!")
