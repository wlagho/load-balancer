import asyncio
import aiohttp
import requests
import matplotlib.pyplot as plt
import time
from collections import defaultdict

async def send_batch_requests(session, url, num_requests):
    """Send a batch of requests and return server response counts"""
    server_counts = defaultdict(int)
    
    tasks = []
    for _ in range(num_requests):
        tasks.append(send_request(session, url))
    
    results = await asyncio.gather(*tasks)
    
    for result in results:
        if result:
            server_counts[result] += 1
    
    return server_counts

async def send_request(session, url):
    """Send a single request and return the server that handled it"""
    try:
        async with session.get(url) as response:
            if response.status == 200:
                data = await response.json()
                message = data.get('message', '')
                if 'Server' in message:
                    return message.split('Server: ')[1] if 'Server: ' in message else message.split('from ')[1]
    except:
        pass
    return None

def add_servers(lb_url, num_servers):
    """Add servers to reach the target number"""
    hostnames = [f"TestServer{i}" for i in range(1, num_servers-2)]  # -3 for existing servers
    payload = {
        "n": num_servers - 3,  # We already have 3 servers
        "hostnames": hostnames
    }
    
    try:
        response = requests.post(f"{lb_url}/add", json=payload)
        return response.status_code == 200
    except:
        return False

def remove_all_test_servers(lb_url):
    """Remove all test servers to reset to original 3"""
    try:
        # Get current replicas
        response = requests.get(f"{lb_url}/rep")
        if response.status_code == 200:
            replicas = response.json()['message']['replicas']
            test_servers = [s for s in replicas if s.startswith('TestServer')]
            
            if test_servers:
                payload = {
                    "n": len(test_servers),
                    "hostnames": test_servers
                }
                requests.delete(f"{lb_url}/rm", json=payload)
    except:
        pass

async def test_scalability(lb_url="http://localhost:5050", num_requests=10000):
    """A-2: Test scalability from N=2 to N=6 servers"""
    print("Starting scalability test...")
    
    results = []
    server_counts_data = []
    
    for n in range(2, 7):  # N = 2 to 6
        print(f"\n--- Testing with N={n} servers ---")
        
        # Reset to 3 servers first
        remove_all_test_servers(lb_url)
        time.sleep(2)
        
        if n > 3:
            # Add servers to reach target N
            success = add_servers(lb_url, n)
            if not success:
                print(f"Failed to add servers for N={n}")
                continue
            time.sleep(3)  # Wait for servers to be ready
        elif n < 3:
            # Remove servers to reach target N
            payload = {"n": 3-n, "hostnames": []}
            requests.delete(f"{lb_url}/rm", json=payload)
            time.sleep(2)
        
        # Verify current server count
        response = requests.get(f"{lb_url}/rep")
        if response.status_code == 200:
            current_servers = len(response.json()['message']['replicas'])
            print(f"Current servers: {current_servers}")
        
        # Run load test
        start_time = time.time()
        
        async with aiohttp.ClientSession() as session:
            server_counts = await send_batch_requests(session, f"{lb_url}/home", num_requests)
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Calculate average load per server
        total_requests = sum(server_counts.values())
        avg_load = total_requests / len(server_counts) if server_counts else 0
        
        results.append({
            'n_servers': n,
            'avg_load': avg_load,
            'total_time': total_time,
            'total_requests': total_requests
        })
        
        server_counts_data.append((n, dict(server_counts)))
        
        print(f"Average load per server: {avg_load:.1f}")
        print(f"Time taken: {total_time:.2f} seconds")
    
    # Create line chart for average load
    n_values = [r['n_servers'] for r in results]
    avg_loads = [r['avg_load'] for r in results]
    
    plt.figure(figsize=(10, 6))
    plt.plot(n_values, avg_loads, marker='o', linewidth=2, markersize=8, color='#FF6B6B')
    plt.title(f'Load Balancer Scalability Analysis\n({num_requests} Requests per Test)')
    plt.xlabel('Number of Servers (N)')
    plt.ylabel('Average Load per Server')
    plt.grid(True, alpha=0.3)
    plt.xticks(n_values)
    
    # Add value labels
    for x, y in zip(n_values, avg_loads):
        plt.annotate(f'{y:.0f}', (x, y), textcoords="offset points", xytext=(0,10), ha='center')
    
    plt.tight_layout()
    plt.savefig('results/scalability.png', dpi=300, bbox_inches='tight')
    plt.show()
    
    return results, server_counts_data

if __name__ == "__main__":
    import os
    os.makedirs('results', exist_ok=True)
    
    asyncio.run(test_scalability())