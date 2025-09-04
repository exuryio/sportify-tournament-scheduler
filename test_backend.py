#!/usr/bin/env python3
"""
Simple test script for Sportify backend API
Run this after starting the backend to verify endpoints work
"""

import requests
import json
from datetime import date, timedelta

BASE_URL = "http://localhost:8000"

def test_health():
    """Test health check endpoint"""
    print("Testing health check...")
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"Health check: {response.status_code} - {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"Health check failed: {e}")
        return False

def test_seed_demo():
    """Test demo data seeding"""
    print("\nTesting demo data seeding...")
    try:
        response = requests.post(f"{BASE_URL}/seed/demo")
        print(f"Demo seeding: {response.status_code} - {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"Demo seeding failed: {e}")
        return False

def test_list_tournaments():
    """Test listing tournaments"""
    print("\nTesting tournament listing...")
    try:
        response = requests.get(f"{BASE_URL}/tournaments")
        print(f"Tournaments: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Found {data['total']} tournaments")
            for tournament in data['tournaments'][:3]:  # Show first 3
                print(f"  - {tournament['name']} ({tournament['sport_type']})")
        return response.status_code == 200
    except Exception as e:
        print(f"Tournament listing failed: {e}")
        return False

def test_list_teams():
    """Test listing teams"""
    print("\nTesting team listing...")
    try:
        response = requests.get(f"{BASE_URL}/teams")
        print(f"Teams: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Found {data['total']} teams")
            for team in data['teams'][:3]:  # Show first 3
                print(f"  - {team['name']} (Captain: {team['captain_name']})")
        return response.status_code == 200
    except Exception as e:
        print(f"Team listing failed: {e}")
        return False

def test_list_courts():
    """Test listing courts"""
    print("\nTesting court listing...")
    try:
        response = requests.get(f"{BASE_URL}/courts")
        print(f"Courts: {response.status_code}")
        if response.status_code == 200:
            courts = response.json()
            print(f"Found {len(courts)} courts")
            for court in courts:
                print(f"  - {court['name']} at {court['location']}")
        return response.status_code == 200
    except Exception as e:
        print(f"Court listing failed: {e}")
        return False

def test_list_time_slots():
    """Test listing time slots"""
    print("\nTesting time slot listing...")
    try:
        response = requests.get(f"{BASE_URL}/time-slots")
        print(f"Time slots: {response.status_code}")
        if response.status_code == 200:
            time_slots = response.json()
            print(f"Found {len(time_slots)} time slots")
            for ts in time_slots[:5]:  # Show first 5
                day_names = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
                day_name = day_names[ts['day_of_week']]
                print(f"  - {day_name} {ts['start_time']}-{ts['end_time']}")
        return response.status_code == 200
    except Exception as e:
        print(f"Time slot listing failed: {e}")
        return False

def test_scheduler():
    """Test the scheduler endpoint"""
    print("\nTesting scheduler...")
    try:
        # First get a tournament ID
        response = requests.get(f"{BASE_URL}/tournaments")
        if response.status_code != 200:
            print("Cannot test scheduler - no tournaments available")
            return False
        
        tournaments = response.json()['tournaments']
        if not tournaments:
            print("Cannot test scheduler - no tournaments available")
            return False
        
        tournament_id = tournaments[0]['id']
        
        # Test scheduler request
        scheduler_request = {
            "tournament_id": tournament_id,
            "week_start_date": date.today().isoformat(),
            "week_end_date": (date.today() + timedelta(days=7)).isoformat(),
            "max_matches_per_team_per_week": 2,
            "fairness_weight": 0.3,
            "court_utilization_weight": 0.4,
            "team_preference_weight": 0.3
        }
        
        response = requests.post(
            f"{BASE_URL}/scheduler/run",
            json=scheduler_request,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"Scheduler: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Schedule created: {data['total_matches']} matches")
            print(f"Fairness score: {data['fairness_score']:.2f}")
            print(f"Court utilization: {data['court_utilization_score']:.2f}")
            print(f"Team preference: {data['team_preference_score']:.2f}")
            print(f"Processing time: {data['processing_time_seconds']:.2f}s")
        else:
            print(f"Scheduler failed: {response.text}")
        
        return response.status_code == 200
    except Exception as e:
        print(f"Scheduler test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 Testing Sportify Backend API")
    print("=" * 50)
    
    tests = [
        test_health,
        test_seed_demo,
        test_list_tournaments,
        test_list_teams,
        test_list_courts,
        test_list_time_slots,
        test_scheduler
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("=" * 50)
    print(f"✅ Tests passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 All tests passed! Backend is working correctly.")
    else:
        print("❌ Some tests failed. Check the backend logs for issues.")

if __name__ == "__main__":
    main()
