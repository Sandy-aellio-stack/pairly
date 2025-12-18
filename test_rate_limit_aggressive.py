#!/usr/bin/env python3
"""
Aggressive rate limiting test to trigger ban mechanism
"""

import requests
import time
from datetime import datetime

BACKEND_URL = "https://datebond.preview.emergentagent.com/api"

def test_aggressive_rate_limiting():
    """Test rate limiting with rapid requests"""
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Starting aggressive rate limiting test...")
    
    session = requests.Session()
    success_count = 0
    rate_limited_count = 0
    
    # Make 200 rapid requests to trigger ban
    for i in range(200):
        try:
            response = session.get(f"{BACKEND_URL}/health", timeout=5)
            
            if response.status_code == 200:
                success_count += 1
            elif response.status_code == 429:
                rate_limited_count += 1
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Rate limited at request {i+1}")
                print(f"  Response: {response.text}")
                print(f"  Headers: {dict(response.headers)}")
                
                if rate_limited_count >= 3:  # Stop after getting rate limited multiple times
                    break
            else:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Unexpected status: {response.status_code}")
            
            # Very small delay
            time.sleep(0.01)
            
        except Exception as e:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Request failed: {e}")
            break
    
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Test completed:")
    print(f"  Successful requests: {success_count}")
    print(f"  Rate limited requests: {rate_limited_count}")
    
    return rate_limited_count > 0

if __name__ == "__main__":
    test_aggressive_rate_limiting()