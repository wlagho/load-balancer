class HashRing:
    def __init__(self, num_nodes=3, ring_size=512, replicas=9):
        self.num_nodes = num_nodes
        self.ring_size = ring_size
        self.replicas = replicas
        self.ring = [None] * ring_size
        self.node_positions = {}  # Track all positions for each node
        self._setup_ring()

    def H(self, i):
        """Hash function for request mapping: H(i) = i²/2 + 2i + 17"""
        return (i * i // 2 + 2 * i + 17) % self.ring_size

    def Phi(self, i, j):
        """Hash function for virtual server mapping: Φ(i,j) = i² + j² + 2j² + 25"""
        return (i * i + j * j + 2 * j * j + 25) % self.ring_size

    def _setup_ring(self):
        """Set up the hash ring with virtual servers"""
        self.node_positions = {i: [] for i in range(self.num_nodes)}
        
        for node_id in range(self.num_nodes):
            for replica_id in range(self.replicas):
                slot = self.Phi(node_id, replica_id)
                original_slot = slot
                
                # Linear probing to handle collisions
                while self.ring[slot] is not None:
                    slot = (slot + 1) % self.ring_size
                    if slot == original_slot:
                        raise Exception("Hash ring is full - cannot place all virtual servers")
                
                self.ring[slot] = node_id
                self.node_positions[node_id].append(slot)

    def get_node_for_request(self, request_id):
        """Get the node that should handle this request using clockwise assignment"""
        slot = self.H(request_id)
        
        # Find the next node in clockwise direction (including the current slot)
        for i in range(self.ring_size):
            current_slot = (slot + i) % self.ring_size
            if self.ring[current_slot] is not None:
                return self.ring[current_slot]
        
        return None  # No nodes available

    def add_node(self, node_id):
        """Add a new node to the hash ring"""
        if node_id in self.node_positions:
            return False  # Node already exists
        
        self.node_positions[node_id] = []
        for replica_id in range(self.replicas):
            slot = self.Phi(node_id, replica_id)
            original_slot = slot
            
            while self.ring[slot] is not None:
                slot = (slot + 1) % self.ring_size
                if slot == original_slot:
                    return False  # Cannot add node
            
            self.ring[slot] = node_id
            self.node_positions[node_id].append(slot)
        
        self.num_nodes += 1
        return True

    def remove_node(self, node_id):
        """Remove a node from the hash ring"""
        if node_id not in self.node_positions:
            return False
        
        # Remove all virtual servers for this node
        for slot in self.node_positions[node_id]:
            self.ring[slot] = None
        
        del self.node_positions[node_id]
        self.num_nodes -= 1
        return True

    def get_ring_status(self):
        """Get current status of the ring"""
        occupied_slots = sum(1 for slot in self.ring if slot is not None)
        return {
            "total_slots": self.ring_size,
            "occupied_slots": occupied_slots,
            "nodes": list(self.node_positions.keys()),
            "virtual_servers_per_node": self.replicas
        }

    def get_load_distribution(self, request_ids):
        """Analyze load distribution for a list of request IDs"""
        load_count = {node_id: 0 for node_id in self.node_positions.keys()}
        
        for req_id in request_ids:
            node = self.get_node_for_request(req_id)
            if node is not None:
                load_count[node] += 1
        
        return load_count

    def get_nodes(self):
        """Get list of active nodes"""
        return list(self.node_positions.keys())
    
    def visualize_ring(self, sample_size=20):
        """Visualize a sample of the ring for debugging"""
        print(f"Ring visualization (showing first {sample_size} slots):")
        for i in range(min(sample_size, self.ring_size)):
            node = self.ring[i] if self.ring[i] is not None else "Empty"
            print(f"Slot {i:3d}: {node}")