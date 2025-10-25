#!/usr/bin/env python3
"""
Test script to verify that registration with all form fields works correctly.
This script tests the registration endpoint with all the new fields.
"""

import requests
import json

# Test data matching the registration form
test_user_data = {
    "username": "testuser123",
    "email": "test@example.com",
    "password": "testpassword123",
    "firstName": "John",
    "lastName": "Doe",
    "title": "Office",
    "officeName": "Test Office Inc.",
    "supplierName": None,
    "location": "United States",
    "phone": "+15551234567"
}

def test_registration():
    """Test the registration endpoint with all form fields."""
    try:
        # Assuming the backend is running on localhost:8000
        response = requests.post(
            "http://localhost:8000/auth/register",
            headers={"Content-Type": "application/json"},
            json=test_user_data
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 200:
            print("✅ Registration successful! All form data was stored.")
            user_data = response.json()
            print(f"User ID: {user_data['id']}")
            print(f"Username: {user_data['username']}")
            print(f"Email: {user_data['email']}")
            print(f"First Name: {user_data['firstName']}")
            print(f"Last Name: {user_data['lastName']}")
            print(f"Title: {user_data['title']}")
            print(f"Office Name: {user_data['officeName']}")
            print(f"Location: {user_data['location']}")
            print(f"Phone: {user_data['phone']}")
        else:
            print("❌ Registration failed!")
            print(f"Error: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to backend. Make sure it's running on localhost:8000")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    print("Testing registration with all form fields...")
    test_registration()
