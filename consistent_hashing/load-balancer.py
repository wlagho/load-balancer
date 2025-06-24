from flask import Flask, jsonify
from consistent_hash import HashRing  

app = Flask(__name__)
hash_ring = HashRing(num_nodes=3, ring_size=512, replicas=9)  

@app.route('/request/<int:request_id>', methods=['GET'])
def route_request(request_id):
    node = hash_ring.get_node_for_request(request_id)  
    if node:
        return jsonify({
            "message": f"Request ID {request_id} routed to {node}",
            "status": "success" 
        }), 200
    else:
        return jsonify({
            "message": "No available node found.",  
            "status": "error"
        }), 503

@app.route('/nodes', methods=['GET'])  
def nodes():  
    return jsonify({
        "node_map": hash_ring.node_map  
    }), 200

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=6000)