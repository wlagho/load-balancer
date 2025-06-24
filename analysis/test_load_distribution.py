import asyncio
import aiohttp
import matplotlib.pyplot as plt
from collections import defaultdict
import time

async def send_request(session, url):
    """Send a single request and return the server that handled it"""
    try:
        async with session.get(url) as response:
            if response.status == 200:
                data = await response.json()
                # Extract server ID from response message
                message = data.get('message', '')
                if 'Server' in message:
                    return message.split('Server: ')[1] if 'Server: ' in message else message.split('from ')[1]
    except:
        pass
    return None

async def test_load_distribution(num_requests=10000, lb_url="http://localhost:5050"):
    """A-1: Test load distribution with 10000 async requests on N=3 servers"""
    print(f"Starting load distribution test with {num_requests} requests...")
    
    server_counts = defaultdict(int)
    start_time = time.time()
    
    async with aiohttp.ClientSession() as session:
        tasks = []
        for _ in range(num_requests):
            task = send_request(session, f"{lb_url}/home")
            tasks.append(task)
        
        # Execute all requests asynchronously
        results = await asyncio.gather(*tasks)
        
        # Count responses from each server
        for result in results:
            if result:
                server_counts[result] += 1
    
    end_time = time.time()
    total_time = end_time - start_time
    
    print(f"Test completed in {total_time:.2f} seconds")
    print("Request distribution:")
    for server, count in server_counts.items():
        print(f"  {server}: {count} requests ({count/num_requests*100:.1f}%)")
    
    # Create bar chart
    servers = list(server_counts.keys())
    counts = list(server_counts.values())
    
    plt.figure(figsize=(10, 6))
    bars = plt.bar(servers, counts, color=['#FF6B6B', '#4ECDC4', '#45B7D1'])
    plt.title(f'Load Distribution Across {len(servers)} Servers\n({num_requests} Async Requests)')
    plt.xlabel('Server')
    plt.ylabel('Number of Requests')
    plt.grid(axis='y', alpha=0.3)
    
    # Add value labels on bars
    for bar, count in zip(bars, counts):
        plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 50, 
                str(count), ha='center', va='bottom')
    
    plt.tight_layout()
    plt.savefig('results/load_distribution.png', dpi=300, bbox_inches='tight')
    plt.show()
    
    return server_counts, total_time

if __name__ == "__main__":
    # Create results directory
    import os
    os.makedirs('results', exist_ok=True)
    
    # Run the test
    asyncio.run(test_load_distribution())