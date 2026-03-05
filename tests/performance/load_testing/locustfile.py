"""
Locust load testing scenarios for RISE farming assistant.

This file defines comprehensive load testing scenarios for:
- Voice processing endpoints
- Image analysis endpoints
- Market intelligence APIs
- Community features
- Resource sharing system

Run with: locust -f locustfile.py --host=https://api.rise.example.com
"""

import json
import base64
import random
import time
from locust import HttpUser, task, between, events
from locust.exception import RescheduleTask


class RISEFarmerUser(HttpUser):
    """
    Simulates a typical farmer user interacting with RISE platform.
    
    User behavior:
    - Voice queries for farming advice
    - Image uploads for crop diagnosis
    - Market price checks
    - Community forum participation
    - Resource sharing interactions
    """
    
    # Wait time between tasks (simulating user think time)
    wait_time = between(5, 15)
    
    def on_start(self):
        """Initialize user session and authenticate."""
        self.user_id = f"farmer_{random.randint(1000, 999999)}"
        self.location = random.choice([
            {"state": "Karnataka", "district": "Bangalore"},
            {"state": "Punjab", "district": "Ludhiana"},
            {"state": "Maharashtra", "district": "Pune"},
            {"state": "Uttar Pradesh", "district": "Lucknow"},
            {"state": "Tamil Nadu", "district": "Coimbatore"}
        ])
        self.language = random.choice(["hi", "en", "ta", "te", "kn", "pa", "mr"])
        self.crops = random.choice([
            ["wheat", "rice"],
            ["cotton", "sugarcane"],
            ["tomato", "potato"],
            ["maize", "soybean"]
        ])
        
        # Authenticate user
        self.authenticate()
    
    def authenticate(self):
        """Authenticate user and get session token."""
        with self.client.post(
            "/api/v1/auth/login",
            json={
                "user_id": self.user_id,
                "phone_number": f"+91{random.randint(7000000000, 9999999999)}"
            },
            catch_response=True,
            name="/auth/login"
        ) as response:
            if response.status_code == 200:
                self.token = response.json().get("token")
                response.success()
            else:
                response.failure(f"Authentication failed: {response.status_code}")
    
    @task(10)
    def voice_query(self):
        """
        Simulate voice query processing.
        Weight: 10 (most common user action)
        Target: <3 seconds response time
        """
        queries = [
            "मेरी गेहूं की फसल में पीले धब्बे हैं, क्या करूं?",
            "What is the best time to plant rice?",
            "ಗೋಧಿ ಬೆಲೆ ಎಷ್ಟು?",
            "ਕਪਾਹ ਦੀ ਕਾਸ਼ਤ ਕਿਵੇਂ ਕਰੀਏ?",
            "టమాటా వ్యాధులు ఎలా నివారించాలి?"
        ]
        
        # Simulate audio data (base64 encoded)
        fake_audio = base64.b64encode(b"fake_audio_data" * 100).decode('utf-8')
        
        start_time = time.time()
        
        with self.client.post(
            "/api/v1/voice/transcribe",
            json={
                "user_id": self.user_id,
                "audio_data": fake_audio,
                "language": self.language
            },
            headers={"Authorization": f"Bearer {self.token}"},
            catch_response=True,
            name="/voice/transcribe"
        ) as response:
            response_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                if response_time < 3000:  # <3s requirement
                    response.success()
                else:
                    response.failure(f"Voice processing too slow: {response_time}ms")
            else:
                response.failure(f"Voice processing failed: {response.status_code}")
    
    @task(8)
    def image_analysis(self):
        """
        Simulate crop disease image analysis.
        Weight: 8 (common user action)
        Target: <10 seconds response time
        """
        # Simulate image data (base64 encoded)
        fake_image = base64.b64encode(b"fake_image_data" * 1000).decode('utf-8')
        
        crop_types = ["wheat", "rice", "cotton", "tomato", "potato", "maize"]
        
        start_time = time.time()
        
        with self.client.post(
            "/api/v1/diagnosis/crop-disease",
            json={
                "user_id": self.user_id,
                "image_data": fake_image,
                "crop_type": random.choice(crop_types),
                "location": self.location
            },
            headers={"Authorization": f"Bearer {self.token}"},
            catch_response=True,
            name="/diagnosis/crop-disease"
        ) as response:
            response_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                if response_time < 10000:  # <10s requirement
                    response.success()
                else:
                    response.failure(f"Image analysis too slow: {response_time}ms")
            else:
                response.failure(f"Image analysis failed: {response.status_code}")
    
    @task(6)
    def check_market_prices(self):
        """
        Check market prices for crops.
        Weight: 6 (frequent user action)
        Target: <1 second response time
        """
        crop = random.choice(self.crops)
        
        with self.client.get(
            f"/api/v1/intelligence/market-prices/{crop}/{self.location['state']}",
            headers={"Authorization": f"Bearer {self.token}"},
            catch_response=True,
            name="/intelligence/market-prices"
        ) as response:
            if response.status_code == 200:
                data = response.json()
                if "prices" in data:
                    response.success()
                else:
                    response.failure("Invalid market price response")
            else:
                response.failure(f"Market price check failed: {response.status_code}")
    
    @task(5)
    def get_weather_forecast(self):
        """
        Get weather forecast for location.
        Weight: 5 (frequent user action)
        Target: <1 second response time
        """
        with self.client.get(
            f"/api/v1/intelligence/weather/{self.location['state']}/{self.location['district']}",
            headers={"Authorization": f"Bearer {self.token}"},
            catch_response=True,
            name="/intelligence/weather"
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Weather forecast failed: {response.status_code}")
    
    @task(4)
    def browse_forum(self):
        """
        Browse community forum discussions.
        Weight: 4 (moderate user action)
        """
        with self.client.get(
            "/api/v1/community/forums",
            params={"language": self.language, "page": 1, "limit": 20},
            headers={"Authorization": f"Bearer {self.token}"},
            catch_response=True,
            name="/community/forums"
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Forum browse failed: {response.status_code}")
    
    @task(3)
    def search_equipment(self):
        """
        Search for available equipment to rent.
        Weight: 3 (moderate user action)
        """
        equipment_types = ["tractor", "pump", "harvester", "drone", "sprayer"]
        
        with self.client.get(
            "/api/v1/community/available-equipment",
            params={
                "location": json.dumps(self.location),
                "equipment_type": random.choice(equipment_types),
                "radius_km": 25
            },
            headers={"Authorization": f"Bearer {self.token}"},
            catch_response=True,
            name="/community/available-equipment"
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Equipment search failed: {response.status_code}")
    
    @task(2)
    def check_government_schemes(self):
        """
        Check eligible government schemes.
        Weight: 2 (occasional user action)
        """
        with self.client.get(
            f"/api/v1/intelligence/schemes/{self.user_id}",
            headers={"Authorization": f"Bearer {self.token}"},
            catch_response=True,
            name="/intelligence/schemes"
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Scheme check failed: {response.status_code}")
    
    @task(2)
    def calculate_profitability(self):
        """
        Calculate crop profitability.
        Weight: 2 (occasional user action)
        """
        with self.client.post(
            "/api/v1/financial/calculate-profitability",
            json={
                "user_id": self.user_id,
                "crop": random.choice(self.crops),
                "land_size": random.uniform(1, 10),
                "location": self.location
            },
            headers={"Authorization": f"Bearer {self.token}"},
            catch_response=True,
            name="/financial/calculate-profitability"
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Profitability calculation failed: {response.status_code}")
    
    @task(1)
    def join_buying_group(self):
        """
        Browse and join cooperative buying groups.
        Weight: 1 (rare user action)
        """
        with self.client.get(
            "/api/v1/community/buying-groups",
            params={"location": json.dumps(self.location)},
            headers={"Authorization": f"Bearer {self.token}"},
            catch_response=True,
            name="/community/buying-groups"
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Buying group browse failed: {response.status_code}")


class RISEPowerUser(HttpUser):
    """
    Simulates a power user (agricultural expert or progressive farmer).
    
    Higher activity level with more advanced features:
    - Posting forum content
    - Listing equipment for sharing
    - Creating buying groups
    - Providing expert advice
    """
    
    wait_time = between(3, 8)
    
    def on_start(self):
        """Initialize power user session."""
        self.user_id = f"expert_{random.randint(1000, 9999)}"
        self.location = random.choice([
            {"state": "Karnataka", "district": "Bangalore"},
            {"state": "Punjab", "district": "Ludhiana"}
        ])
        self.authenticate()
    
    def authenticate(self):
        """Authenticate power user."""
        with self.client.post(
            "/api/v1/auth/login",
            json={
                "user_id": self.user_id,
                "phone_number": f"+91{random.randint(7000000000, 9999999999)}",
                "user_type": "expert"
            },
            catch_response=True,
            name="/auth/login"
        ) as response:
            if response.status_code == 200:
                self.token = response.json().get("token")
                response.success()
    
    @task(5)
    def post_forum_content(self):
        """Post expert advice to forum."""
        with self.client.post(
            "/api/v1/community/discussions",
            json={
                "user_id": self.user_id,
                "title": "Expert farming advice",
                "content": "Best practices for sustainable farming...",
                "category": "best_practices",
                "language": "en"
            },
            headers={"Authorization": f"Bearer {self.token}"},
            catch_response=True,
            name="/community/discussions [POST]"
        ) as response:
            if response.status_code in [200, 201]:
                response.success()
            else:
                response.failure(f"Forum post failed: {response.status_code}")
    
    @task(3)
    def list_equipment(self):
        """List equipment for sharing."""
        with self.client.post(
            "/api/v1/community/list-equipment",
            json={
                "user_id": self.user_id,
                "equipment_type": "tractor",
                "equipment_name": "John Deere 5050D",
                "daily_rate": 2000,
                "location": self.location,
                "available_from": "2024-01-01"
            },
            headers={"Authorization": f"Bearer {self.token}"},
            catch_response=True,
            name="/community/list-equipment"
        ) as response:
            if response.status_code in [200, 201]:
                response.success()
            else:
                response.failure(f"Equipment listing failed: {response.status_code}")
    
    @task(2)
    def create_buying_group(self):
        """Create cooperative buying group."""
        with self.client.post(
            "/api/v1/community/create-buying-group",
            json={
                "organizer_id": self.user_id,
                "group_name": "Fertilizer Buying Group",
                "products": ["urea", "dap"],
                "location": self.location,
                "deadline": "2024-12-31"
            },
            headers={"Authorization": f"Bearer {self.token}"},
            catch_response=True,
            name="/community/create-buying-group"
        ) as response:
            if response.status_code in [200, 201]:
                response.success()
            else:
                response.failure(f"Buying group creation failed: {response.status_code}")


# Custom event handlers for detailed metrics
@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Initialize test metrics."""
    print("🚀 Starting RISE load test...")
    print(f"Target host: {environment.host}")
    print(f"Users: {environment.runner.target_user_count if hasattr(environment.runner, 'target_user_count') else 'N/A'}")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Print test summary."""
    print("\n✅ Load test completed!")
    print(f"Total requests: {environment.stats.total.num_requests}")
    print(f"Total failures: {environment.stats.total.num_failures}")
    print(f"Average response time: {environment.stats.total.avg_response_time:.2f}ms")
    print(f"RPS: {environment.stats.total.total_rps:.2f}")
