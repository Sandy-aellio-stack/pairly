#!/usr/bin/env python3
"""
TrueBond Admin Dashboard API Testing
Comprehensive test suite for TrueBond Admin Dashboard APIs as per review request
"""

import requests
import json
import time
import random
from datetime import datetime
from typing import Dict, Any, Optional, Tuple

# Configuration - Use the correct backend URL from review request
BACKEND_URL = "https://truebond-notify.preview.emergentagent.com/api"

class TrueBondAdminTester:
    def __init__(self):
        self.session = requests.Session()
        self.admin_token = None
        self.moderator_token = None
        self.regular_user_token = None
        self.regular_user_id = None
        self.test_user_ids = []  # For user management testing
        
    def log(self, message: str, level: str = "INFO"):
        """Log test messages with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
        
    def test_health_check(self) -> bool:
        """Test basic API health"""
        try:
            response = self.session.get(f"{BACKEND_URL}/health")
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "healthy" and data.get("service") == "truebond":
                    self.log("✓ Backend health check passed")
                    return True
                else:
                    self.log(f"✗ Backend health check failed - unexpected response: {data}", "ERROR")
                    return False
            else:
                self.log(f"✗ Backend health check failed: {response.status_code}", "ERROR")
                return False
        except Exception as e:
            self.log(f"✗ Backend health check failed: {e}", "ERROR")
            return False
    
    def test_admin_login(self) -> bool:
        """Test admin authentication with provided credentials"""
        try:
            # Test Super Admin login
            admin_login_data = {
                "email": "admin@truebond.com",
                "password": "admin123"
            }
            
            response = self.session.post(f"{BACKEND_URL}/admin/login", json=admin_login_data)
            
            if response.status_code == 200:
                data = response.json()
                if "access_token" in data:
                    self.admin_token = data["access_token"]
                    admin_role = data.get("admin_role", "N/A")
                    admin_name = data.get("admin_name", "N/A")
                    self.log(f"✓ Super Admin login successful - Name: {admin_name}, Role: {admin_role}")
                    
                    # Test Moderator login
                    mod_login_data = {
                        "email": "moderator@truebond.com", 
                        "password": "mod123"
                    }
                    
                    mod_response = self.session.post(f"{BACKEND_URL}/admin/login", json=mod_login_data)
                    
                    if mod_response.status_code == 200:
                        mod_data = mod_response.json()
                        if "access_token" in mod_data:
                            self.moderator_token = mod_data["access_token"]
                            mod_role = mod_data.get("admin_role", "N/A")
                            mod_name = mod_data.get("admin_name", "N/A")
                            self.log(f"✓ Moderator login successful - Name: {mod_name}, Role: {mod_role}")
                            return True
                        else:
                            self.log(f"✗ Moderator login response format incorrect: {mod_data}", "ERROR")
                            return False
                    else:
                        self.log(f"✗ Moderator login failed: {mod_response.status_code}", "ERROR")
                        if mod_response.text:
                            self.log(f"  Response: {mod_response.text}")
                        return False
                else:
                    self.log(f"✗ Admin login response format incorrect: {data}", "ERROR")
                    return False
            else:
                self.log(f"✗ Admin login failed: {response.status_code}", "ERROR")
                if response.text:
                    self.log(f"  Response: {response.text}")
                return False
                
        except Exception as e:
            self.log(f"✗ Admin login test failed: {e}", "ERROR")
            return False
    
    def test_admin_me(self) -> bool:
        """Test GET /admin/me to verify token works"""
        try:
            if not self.admin_token:
                self.log("✗ No admin token available", "ERROR")
                return False
            
            headers = {
                "Authorization": f"Bearer {self.admin_token}",
                "Content-Type": "application/json"
            }
            
            response = self.session.get(f"{BACKEND_URL}/admin/me", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ["email", "role"]
                
                missing_fields = [field for field in required_fields if field not in data]
                if missing_fields:
                    self.log(f"✗ /admin/me missing required fields: {missing_fields}", "ERROR")
                    return False
                
                self.log(f"✓ Admin profile retrieved - Role: {data.get('role')}, Email: {data.get('email')}")
                return True
            else:
                self.log(f"✗ /admin/me failed: {response.status_code}", "ERROR")
                if response.text:
                    self.log(f"  Response: {response.text}")
                return False
                
        except Exception as e:
            self.log(f"✗ /admin/me test failed: {e}", "ERROR")
            return False
    
    def test_admin_analytics_overview(self) -> bool:
        """Test GET /admin/analytics/overview"""
        try:
            if not self.admin_token:
                self.log("✗ No admin token available", "ERROR")
                return False
            
            headers = {
                "Authorization": f"Bearer {self.admin_token}",
                "Content-Type": "application/json"
            }
            
            response = self.session.get(f"{BACKEND_URL}/admin/analytics/overview", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                expected_fields = ["totalUsers", "newUsersToday", "activeUsers"]
                
                missing_fields = [field for field in expected_fields if field not in data]
                if missing_fields:
                    self.log(f"✗ Analytics overview missing fields: {missing_fields}", "ERROR")
                    return False
                
                self.log(f"✓ Analytics overview - Total Users: {data.get('totalUsers')}, New Today: {data.get('newUsersToday')}, Active: {data.get('activeUsers')}")
                return True
            else:
                self.log(f"✗ Analytics overview failed: {response.status_code}", "ERROR")
                if response.text:
                    self.log(f"  Response: {response.text}")
                return False
                
        except Exception as e:
            self.log(f"✗ Analytics overview test failed: {e}", "ERROR")
            return False
    
    def test_admin_analytics_activity(self) -> bool:
        """Test GET /admin/analytics/activity"""
        try:
            if not self.admin_token:
                self.log("✗ No admin token available", "ERROR")
                return False
            
            headers = {
                "Authorization": f"Bearer {self.admin_token}",
                "Content-Type": "application/json"
            }
            
            response = self.session.get(f"{BACKEND_URL}/admin/analytics/activity", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                if "activities" in data:
                    activities = data["activities"]
                    self.log(f"✓ Analytics activity - {len(activities)} recent activities")
                    return True
                else:
                    self.log(f"✗ Analytics activity missing 'activities': {data}", "ERROR")
                    return False
            else:
                self.log(f"✗ Analytics activity failed: {response.status_code}", "ERROR")
                if response.text:
                    self.log(f"  Response: {response.text}")
                return False
                
        except Exception as e:
            self.log(f"✗ Analytics activity test failed: {e}", "ERROR")
            return False
    
    def test_admin_analytics_demographics(self) -> bool:
        """Test GET /admin/analytics/demographics"""
        try:
            if not self.admin_token:
                self.log("✗ No admin token available", "ERROR")
                return False
            
            headers = {
                "Authorization": f"Bearer {self.admin_token}",
                "Content-Type": "application/json"
            }
            
            response = self.session.get(f"{BACKEND_URL}/admin/analytics/demographics", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                # Check for any demographic data structure
                if isinstance(data, dict) and len(data) > 0:
                    self.log(f"✓ Analytics demographics - {len(data)} demographic metrics")
                    for key, value in data.items():
                        if isinstance(value, dict):
                            self.log(f"  {key}: {len(value)} categories")
                        else:
                            self.log(f"  {key}: {value}")
                    return True
                else:
                    self.log(f"✗ Analytics demographics empty or invalid: {data}", "ERROR")
                    return False
            else:
                self.log(f"✗ Analytics demographics failed: {response.status_code}", "ERROR")
                if response.text:
                    self.log(f"  Response: {response.text}")
                return False
                
        except Exception as e:
            self.log(f"✗ Analytics demographics test failed: {e}", "ERROR")
            return False
    
    def test_admin_analytics_highlights(self) -> bool:
        """Test GET /admin/analytics/highlights"""
        try:
            if not self.admin_token:
                self.log("✗ No admin token available", "ERROR")
                return False
            
            headers = {
                "Authorization": f"Bearer {self.admin_token}",
                "Content-Type": "application/json"
            }
            
            response = self.session.get(f"{BACKEND_URL}/admin/analytics/highlights", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                # Highlights should contain today's key stats
                if "today" in data or "highlights" in data or len(data) > 0:
                    self.log(f"✓ Analytics highlights retrieved - {len(data)} highlight metrics")
                    return True
                else:
                    self.log(f"✗ Analytics highlights empty or invalid format: {data}", "ERROR")
                    return False
            else:
                self.log(f"✗ Analytics highlights failed: {response.status_code}", "ERROR")
                if response.text:
                    self.log(f"  Response: {response.text}")
                return False
                
        except Exception as e:
            self.log(f"✗ Analytics highlights test failed: {e}", "ERROR")
            return False
    
    def test_admin_users_list(self) -> bool:
        """Test GET /admin/users - paginated user list"""
        try:
            if not self.admin_token:
                self.log("✗ No admin token available", "ERROR")
                return False
            
            headers = {
                "Authorization": f"Bearer {self.admin_token}",
                "Content-Type": "application/json"
            }
            
            # Test with pagination parameters
            params = {
                "page": 1,
                "limit": 10
            }
            
            response = self.session.get(f"{BACKEND_URL}/admin/users", headers=headers, params=params)
            
            if response.status_code == 200:
                data = response.json()
                expected_fields = ["users", "total"]
                
                missing_fields = [field for field in expected_fields if field not in data]
                if missing_fields:
                    self.log(f"✗ Admin users list missing fields: {missing_fields}", "ERROR")
                    return False
                
                users = data.get("users", [])
                total = data.get("total", 0)
                
                # Store some user IDs for detailed testing
                if users:
                    self.test_user_ids = [user.get("id") for user in users[:3] if user.get("id")]
                
                self.log(f"✓ Admin users list - {len(users)} users returned, {total} total users")
                return True
            else:
                self.log(f"✗ Admin users list failed: {response.status_code}", "ERROR")
                if response.text:
                    self.log(f"  Response: {response.text}")
                return False
                
        except Exception as e:
            self.log(f"✗ Admin users list test failed: {e}", "ERROR")
            return False
    
    def test_admin_user_details(self) -> bool:
        """Test GET /admin/users/{userId} - get detailed user info"""
        try:
            if not self.admin_token:
                self.log("✗ No admin token available", "ERROR")
                return False
            
            if not self.test_user_ids:
                self.log("✗ No test user IDs available", "ERROR")
                return False
            
            headers = {
                "Authorization": f"Bearer {self.admin_token}",
                "Content-Type": "application/json"
            }
            
            # Test with first available user ID
            user_id = self.test_user_ids[0]
            response = self.session.get(f"{BACKEND_URL}/admin/users/{user_id}", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                if "user" in data and "transactions" in data:
                    user = data["user"]
                    transactions = data["transactions"]
                    expected_fields = ["id", "name", "email", "status"]
                    
                    missing_fields = [field for field in expected_fields if field not in user]
                    if missing_fields:
                        self.log(f"✗ Admin user details missing fields: {missing_fields}", "ERROR")
                        return False
                    
                    self.log(f"✓ Admin user details - User: {user.get('name')}, Status: {user.get('status')}, Email: {user.get('email')}, Transactions: {len(transactions)}")
                    return True
                else:
                    self.log(f"✗ Admin user details response format incorrect: {data}", "ERROR")
                    return False
            else:
                self.log(f"✗ Admin user details failed: {response.status_code}", "ERROR")
                if response.text:
                    self.log(f"  Response: {response.text}")
                return False
                
        except Exception as e:
            self.log(f"✗ Admin user details test failed: {e}", "ERROR")
            return False
    
    def test_admin_settings(self) -> bool:
        """Test GET /admin/settings - get app settings"""
        try:
            if not self.admin_token:
                self.log("✗ No admin token available", "ERROR")
                return False
            
            headers = {
                "Authorization": f"Bearer {self.admin_token}",
                "Content-Type": "application/json"
            }
            
            response = self.session.get(f"{BACKEND_URL}/admin/settings", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                expected_fields = ["messageCost", "signupBonus"]
                
                # Check if at least some expected settings are present
                found_fields = [field for field in expected_fields if field in data]
                if not found_fields:
                    self.log(f"✗ Admin settings missing expected fields: {expected_fields}", "ERROR")
                    return False
                
                self.log(f"✓ Admin settings retrieved - {len(data)} settings found")
                for key, value in data.items():
                    self.log(f"  {key}: {value}")
                return True
            else:
                self.log(f"✗ Admin settings failed: {response.status_code}", "ERROR")
                if response.text:
                    self.log(f"  Response: {response.text}")
                return False
                
        except Exception as e:
            self.log(f"✗ Admin settings test failed: {e}", "ERROR")
            return False
    
    def test_admin_settings_pricing(self) -> bool:
        """Test GET /admin/settings/pricing - public endpoint, no auth needed"""
        try:
            # This is a public endpoint, no auth required
            response = self.session.get(f"{BACKEND_URL}/admin/settings/pricing")
            
            if response.status_code == 200:
                data = response.json()
                # Should contain pricing information
                if isinstance(data, dict) and len(data) > 0:
                    self.log(f"✓ Public pricing settings retrieved - {len(data)} pricing items")
                    return True
                else:
                    self.log(f"✗ Public pricing settings empty or invalid: {data}", "ERROR")
                    return False
            else:
                self.log(f"✗ Public pricing settings failed: {response.status_code}", "ERROR")
                if response.text:
                    self.log(f"  Response: {response.text}")
                return False
                
        except Exception as e:
            self.log(f"✗ Public pricing settings test failed: {e}", "ERROR")
            return False
    
    def create_regular_user(self) -> bool:
        """Create a regular user for testing user search and notifications"""
        try:
            timestamp = int(time.time())
            signup_data = {
                "name": "Test User",
                "email": f"testuser{timestamp}@example.com",
                "mobile_number": f"+91987654{timestamp % 10000}",
                "password": "Test@1234",
                "age": 25,
                "gender": "male",
                "interested_in": "female",
                "intent": "dating",
                "min_age": 20,
                "max_age": 35,
                "max_distance_km": 50,
                "address_line": "123 Test St",
                "city": "Mumbai",
                "state": "Maharashtra",
                "country": "India",
                "pincode": "400001"
            }
            
            response = self.session.post(f"{BACKEND_URL}/auth/signup", json=signup_data)
            
            if response.status_code == 200:
                data = response.json()
                self.regular_user_id = data["user_id"]
                self.regular_user_token = data["tokens"]["access_token"]
                self.log("✓ Regular user created for testing")
                return True
            else:
                self.log(f"✗ Regular user creation failed: {response.status_code}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"✗ Regular user creation failed: {e}", "ERROR")
            return False
    
    def test_user_search(self) -> bool:
        """Test GET /search/users - user search functionality"""
        try:
            if not self.regular_user_token:
                self.log("✗ No regular user token available", "ERROR")
                return False
            
            headers = {
                "Authorization": f"Bearer {self.regular_user_token}",
                "Content-Type": "application/json"
            }
            
            # Search for users with query parameter
            params = {"q": "john"}
            
            response = self.session.get(f"{BACKEND_URL}/search/users", headers=headers, params=params)
            
            if response.status_code == 200:
                data = response.json()
                if "results" in data and "total" in data:
                    results = data["results"]
                    total = data["total"]
                    self.log(f"✓ User search successful - Found {total} users matching 'john'")
                    return True
                else:
                    self.log(f"✗ User search response format incorrect: {data}", "ERROR")
                    return False
            else:
                self.log(f"✗ User search failed: {response.status_code}", "ERROR")
                if response.text:
                    self.log(f"  Response: {response.text}")
                return False
                
        except Exception as e:
            self.log(f"✗ User search test failed: {e}", "ERROR")
            return False
    
    def test_notifications(self) -> bool:
        """Test GET /notifications - get user notifications"""
        try:
            if not self.regular_user_token:
                self.log("✗ No regular user token available", "ERROR")
                return False
            
            headers = {
                "Authorization": f"Bearer {self.regular_user_token}",
                "Content-Type": "application/json"
            }
            
            response = self.session.get(f"{BACKEND_URL}/notifications", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                if "notifications" in data:
                    notifications = data["notifications"]
                    self.log(f"✓ Notifications retrieved - {len(notifications)} notifications")
                    return True
                else:
                    self.log(f"✗ Notifications response format incorrect: {data}", "ERROR")
                    return False
            else:
                self.log(f"✗ Notifications failed: {response.status_code}", "ERROR")
                if response.text:
                    self.log(f"  Response: {response.text}")
                return False
                
        except Exception as e:
            self.log(f"✗ Notifications test failed: {e}", "ERROR")
            return False
    
    def test_notifications_unread_count(self) -> bool:
        """Test GET /notifications/unread-count - get unread count"""
        try:
            if not self.regular_user_token:
                self.log("✗ No regular user token available", "ERROR")
                return False
            
            headers = {
                "Authorization": f"Bearer {self.regular_user_token}",
                "Content-Type": "application/json"
            }
            
            response = self.session.get(f"{BACKEND_URL}/notifications/unread-count", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                if "count" in data:
                    unread_count = data["count"]
                    self.log(f"✓ Unread notifications count - {unread_count} unread")
                    return True
                else:
                    self.log(f"✗ Unread count response format incorrect: {data}", "ERROR")
                    return False
            else:
                self.log(f"✗ Unread count failed: {response.status_code}", "ERROR")
                if response.text:
                    self.log(f"  Response: {response.text}")
                return False
                
        except Exception as e:
            self.log(f"✗ Unread count test failed: {e}", "ERROR")
            return False
    
    def run_all_tests(self) -> Dict[str, bool]:
        """Run all TrueBond Admin Dashboard tests"""
        self.log("=" * 80)
        self.log("STARTING TRUEBOND ADMIN DASHBOARD API TESTS")
        self.log(f"Backend URL: {BACKEND_URL}")
        self.log("Testing Admin Credentials:")
        self.log("  Super Admin: admin@truebond.com / admin123")
        self.log("  Moderator: moderator@truebond.com / mod123")
        self.log("=" * 80)
        
        results = {}
        
        # Basic connectivity
        results["health_check"] = self.test_health_check()
        
        if not results["health_check"]:
            self.log("✗ Backend not accessible, stopping tests", "ERROR")
            return results
        
        self.log("-" * 60)
        self.log("TESTING ADMIN AUTHENTICATION")
        self.log("-" * 60)
        
        # Admin authentication
        results["admin_login"] = self.test_admin_login()
        results["admin_me"] = self.test_admin_me()
        
        if not self.admin_token:
            self.log("✗ Admin authentication failed, stopping admin tests", "ERROR")
            return results
        
        self.log("-" * 60)
        self.log("TESTING ADMIN ANALYTICS APIs")
        self.log("-" * 60)
        
        # Admin Analytics APIs
        results["admin_analytics_overview"] = self.test_admin_analytics_overview()
        results["admin_analytics_activity"] = self.test_admin_analytics_activity()
        results["admin_analytics_demographics"] = self.test_admin_analytics_demographics()
        results["admin_analytics_highlights"] = self.test_admin_analytics_highlights()
        
        self.log("-" * 60)
        self.log("TESTING ADMIN USER MANAGEMENT")
        self.log("-" * 60)
        
        # Admin User Management
        results["admin_users_list"] = self.test_admin_users_list()
        results["admin_user_details"] = self.test_admin_user_details()
        
        self.log("-" * 60)
        self.log("TESTING ADMIN SETTINGS")
        self.log("-" * 60)
        
        # Admin Settings
        results["admin_settings"] = self.test_admin_settings()
        results["admin_settings_pricing"] = self.test_admin_settings_pricing()
        
        self.log("-" * 60)
        self.log("TESTING USER FEATURES (Regular User Auth Required)")
        self.log("-" * 60)
        
        # Create regular user for user-specific tests
        if self.create_regular_user():
            results["user_search"] = self.test_user_search()
            results["notifications"] = self.test_notifications()
            results["notifications_unread_count"] = self.test_notifications_unread_count()
        else:
            self.log("✗ Failed to create regular user, skipping user feature tests", "ERROR")
            results["user_creation"] = False
        
        return results
    
    def print_summary(self, results: Dict[str, bool]):
        """Print test summary"""
        self.log("=" * 60)
        self.log("TEST SUMMARY")
        self.log("=" * 60)
        
        passed = sum(1 for result in results.values() if result)
        total = len(results)
        
        # Group results by category
        categories = {
            "Basic Connectivity": ["health_check"],
            "Admin Authentication": ["admin_login", "admin_me"],
            "Admin Analytics APIs": ["admin_analytics_overview", "admin_analytics_activity", "admin_analytics_demographics", "admin_analytics_highlights"],
            "Admin User Management": ["admin_users_list", "admin_user_details"],
            "Admin Settings": ["admin_settings", "admin_settings_pricing"],
            "User Features": ["user_search", "notifications", "notifications_unread_count"]
        }
        
        for category, tests in categories.items():
            self.log(f"\n{category}:")
            for test_name in tests:
                if test_name in results:
                    status = "✓ PASS" if results[test_name] else "✗ FAIL"
                    self.log(f"  {status}: {test_name}")
        
        self.log("-" * 60)
        self.log(f"TOTAL: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
        
        if passed == total:
            self.log("🎉 ALL TESTS PASSED!", "SUCCESS")
        else:
            failed_tests = [name for name, result in results.items() if not result]
            self.log(f"❌ FAILED TESTS: {', '.join(failed_tests)}", "ERROR")

def main():
    """Main test execution"""
    tester = TrueBondAdminTester()
    results = tester.run_all_tests()
    tester.print_summary(results)
    
    # Return exit code based on results
    all_passed = all(results.values())
    return 0 if all_passed else 1

if __name__ == "__main__":
    exit(main())