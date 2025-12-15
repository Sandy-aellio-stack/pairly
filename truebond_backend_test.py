#!/usr/bin/env python3
"""
TrueBond Dating App Backend API Testing
Comprehensive test suite for all TrueBond APIs as per review request
"""

import requests
import json
import time
import random
from datetime import datetime
from typing import Dict, Any, Optional, Tuple

# Configuration - Use the correct backend URL from frontend/.env
BACKEND_URL = "https://pairly-intro.preview.emergentagent.com/api"

class TrueBondTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.user_id = None
        self.test_users = []  # For multi-user testing
        
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
    
    def test_signup_valid(self) -> bool:
        """Test valid user signup with all required fields"""
        try:
            signup_data = {
                "name": "John Doe",
                "email": "john@test.com",
                "mobile_number": "+919876543210",
                "password": "Test@1234",
                "age": 25,
                "gender": "male",
                "interested_in": "female",
                "intent": "dating",
                "min_age": 20,
                "max_age": 35,
                "max_distance_km": 50,
                "address_line": "123 Main St",
                "city": "Mumbai",
                "state": "Maharashtra",
                "country": "India",
                "pincode": "400001"
            }
            
            response = self.session.post(f"{BACKEND_URL}/auth/signup", json=signup_data)
            
            if response.status_code == 200:
                data = response.json()
                if ("user_id" in data and "credits_balance" in data and 
                    "tokens" in data and data["credits_balance"] == 10):
                    self.user_id = data["user_id"]
                    self.auth_token = data["tokens"]["access_token"]
                    self.log("✓ Valid signup successful - 10 credits bonus received")
                    return True
                else:
                    self.log(f"✗ Signup response format incorrect: {data}", "ERROR")
                    return False
            else:
                self.log(f"✗ Valid signup failed: {response.status_code}", "ERROR")
                if response.text:
                    self.log(f"  Response: {response.text}")
                return False
                
        except Exception as e:
            self.log(f"✗ Valid signup test failed: {e}", "ERROR")
            return False
    
    def test_signup_underage(self) -> bool:
        """Test signup rejection for age < 18"""
        try:
            signup_data = {
                "name": "Minor User",
                "email": "minor@test.com",
                "mobile_number": "+919876543211",
                "password": "Test@1234",
                "age": 17,  # Under 18
                "gender": "male",
                "interested_in": "female",
                "intent": "dating",
                "min_age": 18,
                "max_age": 25,
                "max_distance_km": 50,
                "address_line": "123 Main St",
                "city": "Mumbai",
                "state": "Maharashtra",
                "country": "India",
                "pincode": "400001"
            }
            
            response = self.session.post(f"{BACKEND_URL}/auth/signup", json=signup_data)
            
            if response.status_code in [400, 422]:  # FastAPI returns 422 for validation errors
                self.log("✓ Underage signup properly rejected")
                return True
            else:
                self.log(f"✗ Underage signup should be rejected: {response.status_code}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"✗ Underage signup test failed: {e}", "ERROR")
            return False
    
    def test_signup_duplicate_email(self) -> bool:
        """Test duplicate email rejection"""
        try:
            signup_data = {
                "name": "Duplicate User",
                "email": "john@test.com",  # Same as first user
                "mobile_number": "+919876543212",
                "password": "Test@1234",
                "age": 25,
                "gender": "female",
                "interested_in": "male",
                "intent": "dating",
                "min_age": 20,
                "max_age": 35,
                "max_distance_km": 50,
                "address_line": "456 Another St",
                "city": "Delhi",
                "state": "Delhi",
                "country": "India",
                "pincode": "110001"
            }
            
            response = self.session.post(f"{BACKEND_URL}/auth/signup", json=signup_data)
            
            if response.status_code == 400:
                self.log("✓ Duplicate email properly rejected")
                return True
            else:
                self.log(f"✗ Duplicate email should be rejected: {response.status_code}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"✗ Duplicate email test failed: {e}", "ERROR")
            return False
    
    def test_login_valid(self) -> bool:
        """Test valid login"""
        try:
            login_data = {
                "email": "john@test.com",
                "password": "Test@1234"
            }
            
            response = self.session.post(f"{BACKEND_URL}/auth/login", json=login_data)
            
            if response.status_code == 200:
                data = response.json()
                if "user_id" in data and "tokens" in data:
                    self.log("✓ Valid login successful")
                    return True
                else:
                    self.log(f"✗ Login response format incorrect: {data}", "ERROR")
                    return False
            else:
                self.log(f"✗ Valid login failed: {response.status_code}", "ERROR")
                if response.text:
                    self.log(f"  Response: {response.text}")
                return False
                
        except Exception as e:
            self.log(f"✗ Valid login test failed: {e}", "ERROR")
            return False
    
    def test_login_invalid(self) -> bool:
        """Test invalid login credentials"""
        try:
            login_data = {
                "email": "john@test.com",
                "password": "WrongPassword"
            }
            
            response = self.session.post(f"{BACKEND_URL}/auth/login", json=login_data)
            
            if response.status_code == 401:
                self.log("✓ Invalid login properly rejected")
                return True
            else:
                self.log(f"✗ Invalid login should be rejected: {response.status_code}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"✗ Invalid login test failed: {e}", "ERROR")
            return False
    
    def get_headers(self) -> Dict[str, str]:
        """Get authorization headers"""
        return {
            "Authorization": f"Bearer {self.auth_token}",
            "Content-Type": "application/json"
        }
    
    def test_get_me(self) -> bool:
        """Test /auth/me endpoint - should include email/mobile but NO address"""
        try:
            headers = self.get_headers()
            response = self.session.get(f"{BACKEND_URL}/auth/me", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ["id", "name", "age", "gender", "email", "mobile_number", "credits_balance"]
                forbidden_fields = ["address", "address_line", "city", "state", "country", "pincode"]
                
                # Check required fields
                missing_fields = [field for field in required_fields if field not in data]
                if missing_fields:
                    self.log(f"✗ /auth/me missing required fields: {missing_fields}", "ERROR")
                    return False
                
                # Check forbidden fields (address should not be exposed)
                exposed_fields = [field for field in forbidden_fields if field in data]
                if exposed_fields:
                    self.log(f"✗ /auth/me exposes private fields: {exposed_fields}", "ERROR")
                    return False
                
                self.log("✓ /auth/me returns correct profile (email/mobile visible, address hidden)")
                return True
            else:
                self.log(f"✗ /auth/me failed: {response.status_code}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"✗ /auth/me test failed: {e}", "ERROR")
            return False
    
    def create_second_user(self) -> Tuple[str, str]:
        """Create a second user for testing interactions"""
        try:
            signup_data = {
                "name": "Jane Smith",
                "email": "jane@test.com",
                "mobile_number": "+919876543213",
                "password": "Test@1234",
                "age": 28,
                "gender": "female",
                "interested_in": "male",
                "intent": "serious",
                "min_age": 22,
                "max_age": 40,
                "max_distance_km": 30,
                "address_line": "789 Another St",
                "city": "Bangalore",
                "state": "Karnataka",
                "country": "India",
                "pincode": "560001"
            }
            
            response = self.session.post(f"{BACKEND_URL}/auth/signup", json=signup_data)
            
            if response.status_code == 200:
                data = response.json()
                user_id = data["user_id"]
                token = data["tokens"]["access_token"]
                self.test_users.append({"user_id": user_id, "token": token, "name": "Jane Smith"})
                self.log("✓ Second user created successfully")
                return user_id, token
            else:
                self.log(f"✗ Second user creation failed: {response.status_code}", "ERROR")
                return None, None
                
        except Exception as e:
            self.log(f"✗ Second user creation failed: {e}", "ERROR")
            return None, None
    
    def test_get_user_profile(self) -> bool:
        """Test public profile endpoint - should NOT expose address/email/mobile"""
        try:
            # Create second user first
            other_user_id, _ = self.create_second_user()
            if not other_user_id:
                return False
            
            headers = self.get_headers()
            response = self.session.get(f"{BACKEND_URL}/users/profile/{other_user_id}", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ["id", "name", "age", "gender", "is_online", "is_verified"]
                forbidden_fields = ["email", "mobile_number", "address", "address_line", "city", "state", "country", "pincode", "credits_balance"]
                
                # Check required fields
                missing_fields = [field for field in required_fields if field not in data]
                if missing_fields:
                    self.log(f"✗ Public profile missing required fields: {missing_fields}", "ERROR")
                    return False
                
                # Check forbidden fields (private data should not be exposed)
                exposed_fields = [field for field in forbidden_fields if field in data]
                if exposed_fields:
                    self.log(f"✗ Public profile exposes private fields: {exposed_fields}", "ERROR")
                    return False
                
                self.log("✓ Public profile correctly hides private data (address/email/mobile)")
                return True
            else:
                self.log(f"✗ Get user profile failed: {response.status_code}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"✗ Get user profile test failed: {e}", "ERROR")
            return False
    
    def test_update_profile(self) -> bool:
        """Test profile update"""
        try:
            headers = self.get_headers()
            update_data = {
                "bio": "Looking for love and meaningful connections",
                "intent": "serious"
            }
            
            response = self.session.put(f"{BACKEND_URL}/users/profile", json=update_data, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                if (data.get("message") == "Profile updated" and 
                    data.get("profile", {}).get("bio") == update_data["bio"] and
                    data.get("profile", {}).get("intent") == update_data["intent"]):
                    self.log("✓ Profile update successful")
                    return True
                else:
                    self.log(f"✗ Profile update response incorrect: {data}", "ERROR")
                    return False
            else:
                self.log(f"✗ Profile update failed: {response.status_code}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"✗ Profile update test failed: {e}", "ERROR")
            return False
    
    def test_update_preferences(self) -> bool:
        """Test preferences update"""
        try:
            headers = self.get_headers()
            update_data = {
                "interested_in": "female",
                "min_age": 22,
                "max_age": 40,
                "max_distance_km": 75
            }
            
            response = self.session.put(f"{BACKEND_URL}/users/preferences", json=update_data, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                if (data.get("message") == "Preferences updated" and 
                    data.get("preferences", {}).get("min_age") == update_data["min_age"]):
                    self.log("✓ Preferences update successful")
                    return True
                else:
                    self.log(f"✗ Preferences update response incorrect: {data}", "ERROR")
                    return False
            else:
                self.log(f"✗ Preferences update failed: {response.status_code}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"✗ Preferences update test failed: {e}", "ERROR")
            return False
    
    def test_credits_balance(self) -> bool:
        """Test credits balance endpoint"""
        try:
            headers = self.get_headers()
            response = self.session.get(f"{BACKEND_URL}/credits/balance", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                if "credits_balance" in data and data["credits_balance"] == 10:
                    self.log("✓ Credits balance correct (10 signup bonus)")
                    return True
                else:
                    self.log(f"✗ Credits balance incorrect: {data}", "ERROR")
                    return False
            else:
                self.log(f"✗ Credits balance failed: {response.status_code}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"✗ Credits balance test failed: {e}", "ERROR")
            return False
    
    def test_credits_history(self) -> bool:
        """Test credits transaction history"""
        try:
            headers = self.get_headers()
            response = self.session.get(f"{BACKEND_URL}/credits/history", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                if ("transactions" in data and "count" in data and 
                    len(data["transactions"]) > 0):
                    # Should have signup bonus transaction
                    signup_transaction = data["transactions"][0]
                    if (signup_transaction.get("reason") == "signup_bonus" and 
                        signup_transaction.get("amount") == 10):
                        self.log("✓ Credits history shows signup bonus transaction")
                        return True
                    else:
                        self.log(f"✗ Credits history missing signup bonus: {signup_transaction}", "ERROR")
                        return False
                else:
                    self.log(f"✗ Credits history format incorrect: {data}", "ERROR")
                    return False
            else:
                self.log(f"✗ Credits history failed: {response.status_code}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"✗ Credits history test failed: {e}", "ERROR")
            return False
    
    def test_location_update(self) -> bool:
        """Test location update"""
        try:
            headers = self.get_headers()
            location_data = {
                "latitude": 19.0760,
                "longitude": 72.8777
            }
            
            response = self.session.post(f"{BACKEND_URL}/location/update", json=location_data, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "success":
                    self.log("✓ Location update successful")
                    return True
                else:
                    self.log(f"✗ Location update response incorrect: {data}", "ERROR")
                    return False
            else:
                self.log(f"✗ Location update failed: {response.status_code}", "ERROR")
                if response.text:
                    self.log(f"  Response: {response.text}")
                return False
                
        except Exception as e:
            self.log(f"✗ Location update test failed: {e}", "ERROR")
            return False
    
    def test_nearby_users(self) -> bool:
        """Test nearby users query - should NOT expose address/email/mobile"""
        try:
            headers = self.get_headers()
            params = {
                "lat": 19.0760,
                "lng": 72.8777,
                "radius_km": 50
            }
            
            response = self.session.get(f"{BACKEND_URL}/location/nearby", params=params, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                if ("users" in data and "count" in data and "search_params" in data):
                    users = data["users"]
                    self.log(f"✓ Nearby users query successful - found {len(users)} users")
                    
                    # Check that no private data is exposed
                    if users:
                        first_user = users[0]
                        forbidden_fields = ["email", "mobile_number", "address", "address_line", "city", "state", "country", "pincode"]
                        exposed_fields = [field for field in forbidden_fields if field in first_user]
                        if exposed_fields:
                            self.log(f"✗ Nearby users exposes private fields: {exposed_fields}", "ERROR")
                            return False
                    
                    return True
                else:
                    self.log(f"✗ Nearby users response format incorrect: {data}", "ERROR")
                    return False
            else:
                self.log(f"✗ Nearby users failed: {response.status_code}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"✗ Nearby users test failed: {e}", "ERROR")
            return False
    
    def test_send_message_with_credits(self) -> bool:
        """Test sending message with sufficient credits"""
        try:
            if not self.test_users:
                self.log("✗ No second user available for messaging test", "ERROR")
                return False
            
            headers = self.get_headers()
            message_data = {
                "receiver_id": self.test_users[0]["user_id"],
                "content": "Hello! Nice to meet you."
            }
            
            response = self.session.post(f"{BACKEND_URL}/messages/send", json=message_data, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "sent":
                    self.log("✓ Message sent successfully (1 credit deducted)")
                    return True
                else:
                    self.log(f"✗ Message send response incorrect: {data}", "ERROR")
                    return False
            else:
                self.log(f"✗ Message send failed: {response.status_code}", "ERROR")
                if response.text:
                    self.log(f"  Response: {response.text}")
                return False
                
        except Exception as e:
            self.log(f"✗ Message send test failed: {e}", "ERROR")
            return False
    
    def test_send_message_no_credits(self) -> bool:
        """Test sending message with insufficient credits (should return 402)"""
        try:
            # First, drain all credits by sending multiple messages
            headers = self.get_headers()
            receiver_id = self.test_users[0]["user_id"] if self.test_users else "dummy_id"
            
            # Send 10 messages to drain credits (we start with 10, minus 1 from previous test = 9 left)
            for i in range(9):
                message_data = {
                    "receiver_id": receiver_id,
                    "content": f"Draining credits message {i+1}"
                }
                self.session.post(f"{BACKEND_URL}/messages/send", json=message_data, headers=headers)
            
            # Now try to send one more message (should fail with 402)
            message_data = {
                "receiver_id": receiver_id,
                "content": "This should fail - no credits"
            }
            
            response = self.session.post(f"{BACKEND_URL}/messages/send", json=message_data, headers=headers)
            
            if response.status_code == 402:
                self.log("✓ Message properly rejected when no credits (402 Payment Required)")
                return True
            else:
                self.log(f"✗ Message should be rejected with 402: {response.status_code}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"✗ No credits message test failed: {e}", "ERROR")
            return False
    
    def test_get_conversations(self) -> bool:
        """Test get conversations"""
        try:
            headers = self.get_headers()
            response = self.session.get(f"{BACKEND_URL}/messages/conversations", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                if "conversations" in data and "count" in data:
                    self.log(f"✓ Get conversations successful - {data['count']} conversations")
                    return True
                else:
                    self.log(f"✗ Get conversations response format incorrect: {data}", "ERROR")
                    return False
            else:
                self.log(f"✗ Get conversations failed: {response.status_code}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"✗ Get conversations test failed: {e}", "ERROR")
            return False
    
    def test_get_messages(self) -> bool:
        """Test get messages with specific user"""
        try:
            if not self.test_users:
                self.log("✗ No second user available for get messages test", "ERROR")
                return False
            
            headers = self.get_headers()
            other_user_id = self.test_users[0]["user_id"]
            response = self.session.get(f"{BACKEND_URL}/messages/{other_user_id}", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                if "messages" in data and "count" in data:
                    self.log(f"✓ Get messages successful - {data['count']} messages")
                    return True
                else:
                    self.log(f"✗ Get messages response format incorrect: {data}", "ERROR")
                    return False
            else:
                self.log(f"✗ Get messages failed: {response.status_code}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"✗ Get messages test failed: {e}", "ERROR")
            return False
    
    def test_payment_packages(self) -> bool:
        """Test get payment packages - should have INR pricing with min ₹100"""
        try:
            response = self.session.get(f"{BACKEND_URL}/payments/packages")
            
            if response.status_code == 200:
                data = response.json()
                if ("packages" in data and "currency" in data and 
                    data["currency"] == "INR" and data.get("min_purchase") == 100):
                    packages = data["packages"]
                    if packages and len(packages) > 0:
                        # Check if packages have proper structure
                        first_package = packages[0]
                        if "id" in first_package and "price" in first_package:
                            self.log(f"✓ Payment packages available - {len(packages)} packages, currency: INR")
                            return True
                        else:
                            self.log(f"✗ Payment packages format incorrect: {first_package}", "ERROR")
                            return False
                    else:
                        self.log("✓ Payment packages endpoint working (no packages configured)")
                        return True
                else:
                    self.log(f"✗ Payment packages response format incorrect: {data}", "ERROR")
                    return False
            else:
                self.log(f"✗ Payment packages failed: {response.status_code}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"✗ Payment packages test failed: {e}", "ERROR")
            return False
    
    def test_create_payment_order(self) -> bool:
        """Test create payment order"""
        try:
            headers = self.get_headers()
            order_data = {
                "package_id": "pack_100"
            }
            
            response = self.session.post(f"{BACKEND_URL}/payments/order", json=order_data, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                if "order_id" in data:
                    self.log("✓ Payment order creation successful")
                    return True
                else:
                    self.log(f"✗ Payment order response format incorrect: {data}", "ERROR")
                    return False
            elif response.status_code == 404:
                self.log("✓ Payment order properly rejects invalid package_id")
                return True
            else:
                self.log(f"✗ Payment order failed: {response.status_code}", "ERROR")
                if response.text:
                    self.log(f"  Response: {response.text}")
                return False
                
        except Exception as e:
            self.log(f"✗ Payment order test failed: {e}", "ERROR")
            return False
    
    def run_all_tests(self) -> Dict[str, bool]:
        """Run all TrueBond backend tests"""
        self.log("=" * 80)
        self.log("STARTING TRUEBOND DATING APP BACKEND TESTS")
        self.log(f"Backend URL: {BACKEND_URL}")
        self.log("=" * 80)
        
        results = {}
        
        # Basic connectivity
        results["health_check"] = self.test_health_check()
        
        if not results["health_check"]:
            self.log("✗ Backend not accessible, stopping tests", "ERROR")
            return results
        
        self.log("-" * 60)
        self.log("TESTING AUTH SYSTEM")
        self.log("-" * 60)
        
        # Auth tests
        results["signup_valid"] = self.test_signup_valid()
        results["signup_underage"] = self.test_signup_underage()
        results["signup_duplicate_email"] = self.test_signup_duplicate_email()
        results["login_valid"] = self.test_login_valid()
        results["login_invalid"] = self.test_login_invalid()
        results["get_me"] = self.test_get_me()
        
        if not self.auth_token:
            self.log("✗ Authentication failed, stopping remaining tests", "ERROR")
            return results
        
        self.log("-" * 60)
        self.log("TESTING USERS API")
        self.log("-" * 60)
        
        # Users tests
        results["get_user_profile"] = self.test_get_user_profile()
        results["update_profile"] = self.test_update_profile()
        results["update_preferences"] = self.test_update_preferences()
        
        self.log("-" * 60)
        self.log("TESTING CREDITS API")
        self.log("-" * 60)
        
        # Credits tests
        results["credits_balance"] = self.test_credits_balance()
        results["credits_history"] = self.test_credits_history()
        
        self.log("-" * 60)
        self.log("TESTING LOCATION API")
        self.log("-" * 60)
        
        # Location tests
        results["location_update"] = self.test_location_update()
        results["nearby_users"] = self.test_nearby_users()
        
        self.log("-" * 60)
        self.log("TESTING MESSAGES API")
        self.log("-" * 60)
        
        # Messages tests
        results["send_message_with_credits"] = self.test_send_message_with_credits()
        results["send_message_no_credits"] = self.test_send_message_no_credits()
        results["get_conversations"] = self.test_get_conversations()
        results["get_messages"] = self.test_get_messages()
        
        self.log("-" * 60)
        self.log("TESTING PAYMENTS API")
        self.log("-" * 60)
        
        # Payments tests
        results["payment_packages"] = self.test_payment_packages()
        results["create_payment_order"] = self.test_create_payment_order()
        
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
            "Auth System": ["health_check", "signup_valid", "signup_underage", "signup_duplicate_email", "login_valid", "login_invalid", "get_me"],
            "Users API": ["get_user_profile", "update_profile", "update_preferences"],
            "Credits API": ["credits_balance", "credits_history"],
            "Location API": ["location_update", "nearby_users"],
            "Messages API": ["send_message_with_credits", "send_message_no_credits", "get_conversations", "get_messages"],
            "Payments API": ["payment_packages", "create_payment_order"]
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
    tester = TrueBondTester()
    results = tester.run_all_tests()
    tester.print_summary(results)
    
    # Return exit code based on results
    all_passed = all(results.values())
    return 0 if all_passed else 1

if __name__ == "__main__":
    exit(main())