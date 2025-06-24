import os
import json
import random
import string
import requests
from flask import Flask, request, jsonify
from consistent_hash import HashRing

app = Flask(__name__)

class LoadBalancer:
    def __init__(self):
        self.hash_ring = HashRing(num_nodes=0, ring_size=512, replicas=9)
        self.servers = {}  # hostname -> node_id
        self.node_to_hostname = {}  # node_id -> hostname
        self.next_node_id = 0
        
        # Register existing servers from docker-compose
        self._register_existing_server("Server1")
        self._register_existing_server("Server2") 
        self._register_existing_server("Server3")
    
    def _register_existing_server(self, hostname):
        """Register an existing server container in the hash ring"""
        if hostname not in self.servers:
            node_id = self.next_node_id
            self.hash_ring.add_node(node_id)
            self.servers[hostname] = node_id
            self.node_to_hostname[node_id] = hostname
            self.next_node_id += 1
            print(f"Registered existing server: {hostname} (node_id: {node_id})")
    
    def _generate_hostname(self):
        return ''.join(random.choices(string.ascii_letters + string.digits, k=8))
    
    def _spawn_server(self, hostname=None):
        if hostname is None:
            hostname = self._generate_hostname()
        
        if hostname in self.servers:
            return False
        
        cmd = f"sudo docker run --name {hostname} --network net1 --network-alias {hostname} -e SERVER_ID={hostname} -d server:latest"
        result = os.popen(cmd).read().strip()
        
        if result:
            node_id = self.next_node_id
            self.hash_ring.add_node(node_id)
            self.servers[hostname] = node_id
            self.node_to_hostname[node_id] = hostname
            self.next_node_id += 1
            return True
        return False
    
    def _remove_server(self, hostname):
        if hostname not in self.servers:
            return False
        
        os.system(f'sudo docker stop {hostname} && sudo docker rm {hostname}')
        node_id = self.servers[hostname]
        self.hash_ring.remove_node(node_id)
        del self.servers[hostname]
        del self.node_to_hostname[node_id]
        return True

lb = LoadBalancer()

@app.route('/rep', methods=['GET'])
def get_replicas():
    replicas = list(lb.servers.keys())
    return jsonify({
        "message": {
            "N": len(replicas),
            "replicas": replicas
        },
        "status": "successful"
    }), 200

@app.route('/add', methods=['POST'])
def add_servers():
    data = request.get_json()
    n = data.get('n', 0)
    hostnames = data.get('hostnames', [])
    
    if len(hostnames) > n:
        return jsonify({
            "message": "<Error> Length of hostname list is more than newly added instances",
            "status": "failure"
        }), 400
    
    # Add servers with provided hostnames
    for i in range(n):
        hostname = hostnames[i] if i < len(hostnames) else None
        lb._spawn_server(hostname)
    
    replicas = list(lb.servers.keys())
    return jsonify({
        "message": {
            "N": len(replicas),
            "replicas": replicas
        },
        "status": "successful"
    }), 200

@app.route('/rm', methods=['DELETE'])
def remove_servers():
    data = request.get_json()
    n = data.get('n', 0)
    hostnames = data.get('hostnames', [])
    
    if len(hostnames) > n:
        return jsonify({
            "message": "<Error> Length of hostname list is more than removable instances",
            "status": "failure"
        }), 400
    
    # Remove specified servers
    removed = 0
    for hostname in hostnames:
        if hostname in lb.servers and removed < n:
            lb._remove_server(hostname)
            removed += 1
    
    # Remove additional random servers if needed
    remaining_servers = list(lb.servers.keys())
    while removed < n and remaining_servers:
        hostname = random.choice(remaining_servers)
        lb._remove_server(hostname)
        remaining_servers.remove(hostname)
        removed += 1
    
    replicas = list(lb.servers.keys())
    return jsonify({
        "message": {
            "N": len(replicas),
            "replicas": replicas
        },
        "status": "successful"
    }), 200

@app.route('/<path:path>', methods=['GET'])
def route_request(path):
    if not lb.servers:
        return jsonify({
            "message": "<Error> No server replicas available",
            "status": "failure"
        }), 500
    
    # Generate request ID (6-digit number as per assignment)
    request_id = random.randint(100000, 999999)
    
    # Get node from hash ring
    node_id = lb.hash_ring.get_node_for_request(request_id)
    if node_id is None:
        return jsonify({
            "message": "<Error> No server available",
            "status": "failure"
        }), 500
    
    hostname = lb.node_to_hostname[node_id]
    
    try:
        # Forward request to selected server
        response = requests.get(f'http://{hostname}:5000/{path}', timeout=5)
        return response.json(), response.status_code
    except:
        return jsonify({
            "message": f"<Error> '/{path}' endpoint does not exist in server replicas",
            "status": "failure"
        }), 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)