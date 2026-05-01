"""
Tests for the Mergington High School Activities API
"""

import pytest
from fastapi.testclient import TestClient
from src.app import app, activities


@pytest.fixture
def client():
    """Create a test client with a fresh app instance"""
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_activities():
    """Reset activities to a known state before each test"""
    activities.clear()
    activities.update({
        "Chess Club": {
            "description": "Learn strategies and compete in chess tournaments",
            "schedule": "Fridays, 3:30 PM - 5:00 PM",
            "max_participants": 12,
            "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
        },
        "Programming Class": {
            "description": "Learn programming fundamentals and build software projects",
            "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
            "max_participants": 20,
            "participants": ["emma@mergington.edu", "sophia@mergington.edu"]
        },
        "Gym Class": {
            "description": "Physical education and sports activities",
            "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
            "max_participants": 30,
            "participants": ["john@mergington.edu", "olivia@mergington.edu"]
        }
    })


class TestRootEndpoint:
    """Tests for GET / endpoint"""

    def test_root_redirect(self, client):
        """Test that root endpoint redirects to index.html"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"


class TestActivitiesEndpoint:
    """Tests for GET /activities endpoint"""

    def test_get_activities_success(self, client):
        """Test that GET /activities returns all activities"""
        response = client.get("/activities")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
        assert "Chess Club" in data
        assert "Programming Class" in data
        assert "Gym Class" in data

    def test_get_activities_structure(self, client):
        """Test that activities have the correct structure"""
        response = client.get("/activities")
        data = response.json()
        activity = data["Chess Club"]
        assert "description" in activity
        assert "schedule" in activity
        assert "max_participants" in activity
        assert "participants" in activity
        assert isinstance(activity["participants"], list)

    def test_get_activities_participants(self, client):
        """Test that participants are correctly returned"""
        response = client.get("/activities")
        data = response.json()
        assert "michael@mergington.edu" in data["Chess Club"]["participants"]
        assert "daniel@mergington.edu" in data["Chess Club"]["participants"]


class TestSignupEndpoint:
    """Tests for POST /activities/{activity_name}/signup endpoint"""

    def test_signup_success(self, client):
        """Test successful signup for an activity"""
        response = client.post(
            "/activities/Chess Club/signup?email=newstudent@mergington.edu"
        )
        assert response.status_code == 200
        data = response.json()
        assert "Signed up" in data["message"]
        assert "newstudent@mergington.edu" in data["message"]

    def test_signup_adds_participant(self, client):
        """Test that signup adds participant to activity"""
        client.post("/activities/Chess Club/signup?email=newstudent@mergington.edu")
        response = client.get("/activities")
        activity = response.json()["Chess Club"]
        assert "newstudent@mergington.edu" in activity["participants"]

    def test_signup_duplicate_email(self, client):
        """Test that duplicate signup returns error"""
        response = client.post(
            "/activities/Chess Club/signup?email=michael@mergington.edu"
        )
        assert response.status_code == 400
        data = response.json()
        assert "already signed up" in data["detail"].lower()

    def test_signup_activity_not_found(self, client):
        """Test signup to non-existent activity returns 404"""
        response = client.post(
            "/activities/Nonexistent Club/signup?email=student@mergington.edu"
        )
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()

    def test_signup_multiple_students(self, client):
        """Test multiple different students can sign up"""
        client.post("/activities/Chess Club/signup?email=student1@mergington.edu")
        client.post("/activities/Chess Club/signup?email=student2@mergington.edu")
        
        response = client.get("/activities")
        participants = response.json()["Chess Club"]["participants"]
        assert "student1@mergington.edu" in participants
        assert "student2@mergington.edu" in participants


class TestRemoveParticipantEndpoint:
    """Tests for DELETE /activities/{activity_name}/signup endpoint"""

    def test_remove_participant_success(self, client):
        """Test successful removal of a participant"""
        response = client.delete(
            "/activities/Chess Club/signup?email=michael@mergington.edu"
        )
        assert response.status_code == 200
        data = response.json()
        assert "Removed" in data["message"]
        assert "michael@mergington.edu" in data["message"]

    def test_remove_participant_verifies_removal(self, client):
        """Test that participant is actually removed from activity"""
        client.delete(
            "/activities/Chess Club/signup?email=michael@mergington.edu"
        )
        response = client.get("/activities")
        participants = response.json()["Chess Club"]["participants"]
        assert "michael@mergington.edu" not in participants
        assert "daniel@mergington.edu" in participants

    def test_remove_nonexistent_participant(self, client):
        """Test removing non-existent participant returns 404"""
        response = client.delete(
            "/activities/Chess Club/signup?email=notexist@mergington.edu"
        )
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()

    def test_remove_from_nonexistent_activity(self, client):
        """Test removing participant from non-existent activity returns 404"""
        response = client.delete(
            "/activities/Nonexistent Club/signup?email=michael@mergington.edu"
        )
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()

    def test_remove_and_rejoin(self, client):
        """Test that a participant can be removed and re-added"""
        # Remove participant
        client.delete(
            "/activities/Chess Club/signup?email=michael@mergington.edu"
        )
        
        # Verify removal
        response = client.get("/activities")
        assert "michael@mergington.edu" not in response.json()["Chess Club"]["participants"]
        
        # Re-add participant
        response = client.post(
            "/activities/Chess Club/signup?email=michael@mergington.edu"
        )
        assert response.status_code == 200
        
        # Verify re-added
        response = client.get("/activities")
        assert "michael@mergington.edu" in response.json()["Chess Club"]["participants"]
