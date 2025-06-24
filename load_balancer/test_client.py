#!/usr/bin/env python3

import requests
import json
import time
import asyncio
import aiohttp
from collections import defaultdict
import matplotlib.pyplot as plt

class LoadBalancerTester:
    def __init__(self, base_url="http://localhost:5000"):
        self.base_url = base_url

    def test_endpoints(self):
        """Test all load balancer endpoints"""
        print("=== Testing Load Balancer Endpoints ===")
        
        # Test /rep endpoint
        print("\n1. Testing /rep endpoint:")
        try:
            response = requests.get(f"{self.base_url}/rep")
            print(f"Status: {response.status_code}")
            print(f"Response: {json.dumps(response.json(), indent=2)}")
        except Exception as e:
            print(f"Error: {e}")

        # Test /home endpoint
        print("\n2. Testing /home endpoint:")
        try:
            response = requests.get(f"{self.base_url}/home")
            print(f"Status: {response.status_code}")
            print(f"Response: {json.dumps(response.json(), indent=2)}")
        except Exception as e:
            print(f"Error: {e}")

        # Test adding servers
        print("\n3. Testing /add endpoint:")
        try:
            payload = {"n": 2, "hostnames": ["TestServer1", "TestServer2"]}
            response = requests.post(f"{self.base_url}/add", json=payload)
            print(f"Status: {response.status_code}")
            print(f"Response: {json.dumps(response.json(), indent=2)}")
        except Exception as e:
            print(f"Error: {e}")

        # Test removing servers
        print("\n4. Testing /rm endpoint:")
        try:
            payload = {"n": 1, "hostnames": ["TestServer1"]}
            response = requests.delete(f"{self.base_url}/rm", json=payload)
            print(f"Status: {response.status_code}")
            print(f"Response: {json.dumps(response.json(), indent=2)}")
        except Exception as e:
            print(f"Error: {e}")

    async def make_async_request(self, session, url):
        """Make an async HTTP request"""
        try:
            async with session.get(url, timeout=5) as response:
                if response.status == 200:
                    data = await response.json()
                    return data['message'].split(':')[1].strip()
        except:
            pass
        return None

    async def run_load_test(self, num_requests=10000):
        """Run async load test"""
        print(f"\n=== Running Load Test ({num_requests} requests) ===")
        
        async with aiohttp.ClientSession() as session:
            tasks = []
            for _ in range(num_requests):
                task = self.make_async_request(session, f"{self.base_url}/home")
                tasks.append(task)
            
            print("Sending requests...")
            results = await asyncio.gather(*tasks)
            
        # Count responses per server
        server_counts = defaultdict(int)
        successful_requests = 0
        
        for result in results:
            if result:
                server_counts[result] += 1
                successful_requests += 1
        
        print(f"\nLoad Distribution ({successful_requests}/{num_requests} successful):")
        for server, count in sorted(server_counts.items()):
            percentage = (count / successful_requests) * 100 if successful_requests > 0 else 0
            print(f"  {server}: {count} requests ({percentage:.2f}%)")
        
        return server_counts

    def test_scalability(self):
        """Test scalability with different numbers of servers"""
        print("\n=== Testing Scalability ===")
        
        results = {}
        
        for n in range(2, 7):  # Test with 2 to 6 servers
            print(f"\nTesting with N = {n} servers...")
            
            # Reset to 3 servers first
            self._reset_servers()
            time.sleep(2)
            
            # Adjust to desired number
            current_servers = self._get_current_server_count()
            if current_servers < n:
                # Add servers
                to_add = n - current_servers
                payload = {"n": to_add}
                response = requests.post(f"{self.base_url}/add", json=payload)
                print(f"Added {to_add} servers: {response.status_code}")
            elif current_servers > n:
                # Remove servers
                to_remove = current_servers - n
                payload = {"n": to_remove}
                response = requests.delete