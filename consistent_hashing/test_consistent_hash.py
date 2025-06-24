#!/usr/bin/env python3

from consistent_hash import HashRing
import random

def test_hash_functions():
    """Test the hash functions with sample values"""
    print("=== Testing Hash Functions ===")
    hr = HashRing()
    
    # Test H(i) function
    print("H(i) function tests:")
    for i in [1, 100, 500, 1000]:
        result = hr.H(i)
        print(f"H({i}) = {result}")
    
    # Test Phi(i,j) function  
    print("\nΦ(i,j) function tests:")
    for i in range(3):
        for j in range(3):
            result = hr.Phi(i, j)
            print(f"Φ({i},{j}) = {result}")

def test_ring_setup():
    """Test ring setup and virtual server placement"""
    print("\n=== Testing Ring Setup ===")
    hr = HashRing(num_nodes=3, ring_size=512, replicas=9)
    
    status = hr.get_ring_status()
    print(f"Ring Status: {status}")
    
    # Show where each node's virtual servers are placed
    for node_id, positions in hr.node_positions.items():
        print(f"Node {node_id} virtual servers at slots: {sorted(positions)}")

def test_request_routing():
    """Test request routing to nodes"""
    print("\n=== Testing Request Routing ===")
    hr = HashRing()
    
    # Test with some sample request IDs
    sample_requests = [123456, 789012, 345678, 901234, 567890]
    
    for req_id in sample_requests:
        node = hr.get_node_for_request(req_id)
        slot = hr.H(req_id)
        print(f"Request {req_id} -> Slot {slot} -> Node {node}")

def test_load_distribution():
    """Test load distribution with many requests"""
    print("\n=== Testing Load Distribution ===")
    hr = HashRing()
    
    # Generate 10000 random request IDs
    request_ids = [random.randint(100000, 999999) for _ in range(10000)]
    
    load_distribution = hr.get_load_distribution(request_ids)
    
    print("Load distribution for 10,000 requests:")
    total_requests = sum(load_distribution.values())
    for node_id, count in load_distribution.items():
        percentage = (count / total_requests) * 100 if total_requests > 0 else 0
        print(f"Node {node_id}: {count} requests ({percentage:.2f}%)")

def test_node_operations():
    """Test adding and removing nodes"""
    print("\n=== Testing Node Operations ===")
    hr = HashRing(num_nodes=3)
    
    print("Initial state:")
    print(f"Nodes: {list(hr.node_positions.keys())}")
    
    # Add a new node
    print("\nAdding Node 3...")
    success = hr.add_node(3)
    print(f"Add successful: {success}")
    print(f"Nodes: {list(hr.node_positions.keys())}")
    
    # Remove a node
    print("\nRemoving Node 1...")
    success = hr.remove_node(1)
    print(f"Remove successful: {success}")
    print(f"Nodes: {list(hr.node_positions.keys())}")

if __name__ == "__main__":
    print("Consistent Hashing Implementation Test")
    print("=" * 50)
    
    test_hash_functions()
    test_ring_setup()
    test_request_routing()
    test_load_distribution()
    test_node_operations()
    
    print("\n" + "=" * 50)
    print("Testing completed!")