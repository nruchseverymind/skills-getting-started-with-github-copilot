"""Tests for the Mergington High School API"""

import pytest
from fastapi import HTTPException


class TestGetActivities:
    """Tests for GET /activities endpoint"""
    
    def test_get_activities_returns_all_activities(self, client):
        """Test that GET /activities returns all activities"""
        response = client.get("/activities")
        assert response.status_code == 200
        
        activities = response.json()
        assert len(activities) == 9
        assert "Chess Club" in activities
        assert "Programming Class" in activities
        assert "Gym Class" in activities
    
    def test_activities_have_required_fields(self, client):
        """Test that activities have all required fields"""
        response = client.get("/activities")
        activities = response.json()
        
        for activity_name, activity_details in activities.items():
            assert "description" in activity_details
            assert "schedule" in activity_details
            assert "max_participants" in activity_details
            assert "participants" in activity_details
            assert isinstance(activity_details["participants"], list)
    
    def test_activities_have_participants(self, client):
        """Test that activities contain participant data"""
        response = client.get("/activities")
        activities = response.json()
        
        # Chess Club should have 2 participants
        assert len(activities["Chess Club"]["participants"]) == 2
        assert "michael@mergington.edu" in activities["Chess Club"]["participants"]
        assert "daniel@mergington.edu" in activities["Chess Club"]["participants"]


class TestSignupForActivity:
    """Tests for POST /activities/{activity_name}/signup endpoint"""
    
    def test_signup_success(self, client):
        """Test successful signup for an activity"""
        email = "newstudent@mergington.edu"
        activity = "Tennis Club"
        
        response = client.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert email in data["message"]
        assert activity in data["message"]
    
    def test_signup_adds_participant(self, client):
        """Test that signup actually adds the participant"""
        email = "newstudent@mergington.edu"
        activity = "Tennis Club"
        
        # Get initial participant count
        response = client.get("/activities")
        initial_count = len(response.json()[activity]["participants"])
        
        # Sign up
        client.post(f"/activities/{activity}/signup", params={"email": email})
        
        # Verify participant was added
        response = client.get("/activities")
        new_count = len(response.json()[activity]["participants"])
        assert new_count == initial_count + 1
        assert email in response.json()[activity]["participants"]
    
    def test_signup_duplicate_student_fails(self, client):
        """Test that duplicate signup returns error"""
        email = "michael@mergington.edu"  # Already in Chess Club
        activity = "Chess Club"
        
        response = client.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "already signed up" in data["detail"]
    
    def test_signup_nonexistent_activity_fails(self, client):
        """Test that signup for non-existent activity returns error"""
        response = client.post(
            "/activities/Nonexistent Activity/signup",
            params={"email": "test@mergington.edu"}
        )
        
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"]
    
    def test_signup_multiple_activities(self, client):
        """Test that a student can signup for multiple activities"""
        email = "multiactivity@mergington.edu"
        
        # Sign up for Chess Club
        response1 = client.post(
            "/activities/Chess Club/signup",
            params={"email": email}
        )
        assert response1.status_code == 200
        
        # Sign up for Programming Class
        response2 = client.post(
            "/activities/Programming Class/signup",
            params={"email": email}
        )
        assert response2.status_code == 200
        
        # Verify both signups
        response = client.get("/activities")
        activities = response.json()
        assert email in activities["Chess Club"]["participants"]
        assert email in activities["Programming Class"]["participants"]


class TestUnregisterFromActivity:
    """Tests for POST /activities/{activity_name}/unregister endpoint"""
    
    def test_unregister_success(self, client):
        """Test successful unregister from an activity"""
        email = "michael@mergington.edu"
        activity = "Chess Club"
        
        response = client.post(
            f"/activities/{activity}/unregister",
            params={"email": email}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert email in data["message"]
        assert activity in data["message"]
    
    def test_unregister_removes_participant(self, client):
        """Test that unregister actually removes the participant"""
        email = "michael@mergington.edu"
        activity = "Chess Club"
        
        # Verify participant exists
        response = client.get("/activities")
        assert email in response.json()[activity]["participants"]
        
        # Unregister
        client.post(f"/activities/{activity}/unregister", params={"email": email})
        
        # Verify participant was removed
        response = client.get("/activities")
        assert email not in response.json()[activity]["participants"]
    
    def test_unregister_nonexistent_student_fails(self, client):
        """Test that unregistering a non-participant returns error"""
        response = client.post(
            "/activities/Chess Club/unregister",
            params={"email": "nonexistent@mergington.edu"}
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "not signed up" in data["detail"]
    
    def test_unregister_nonexistent_activity_fails(self, client):
        """Test that unregister from non-existent activity returns error"""
        response = client.post(
            "/activities/Nonexistent Activity/unregister",
            params={"email": "test@mergington.edu"}
        )
        
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"]
    
    def test_signup_after_unregister(self, client):
        """Test that a student can sign up again after unregistering"""
        email = "michael@mergington.edu"
        activity = "Chess Club"
        
        # Unregister
        client.post(f"/activities/{activity}/unregister", params={"email": email})
        
        # Verify unregistered
        response = client.get("/activities")
        assert email not in response.json()[activity]["participants"]
        
        # Sign up again
        response = client.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )
        assert response.status_code == 200
        
        # Verify re-signed up
        response = client.get("/activities")
        assert email in response.json()[activity]["participants"]


class TestRootEndpoint:
    """Tests for root endpoint"""
    
    def test_root_redirects_to_static(self, client):
        """Test that root endpoint redirects to static files"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307  # Temporary redirect
        assert "/static/index.html" in response.headers["location"]
