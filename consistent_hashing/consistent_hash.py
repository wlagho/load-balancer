class HashRing: 
    def __init__(self, num_nodes=3, ring_size=512, replicas=9):  
        self.num_nodes = num_nodes  
        self.ring_size = ring_size  
        self.replicas = replicas    
        self.ring = [None] * ring_size  
        self.node_map = {}  
        self._setup_ring()  

    def H(self, i):
        hash_value = pow(i, 2) + 3*i + 23  
        return hash_value % self.ring_size

    def Phi(self, i, j):
        key = f"{i}-{j}"
        hash_value = pow(i, 2) + pow(j, 2) + 3*j + 31  
        return hash_value % self.ring_size

    def _setup_ring(self):  
        for node_id in range(self.num_nodes):  
            for replica_id in range(self.replicas):
                slot = self.Phi(node_id, replica_id)
                original_slot = slot
                while self.ring[slot] is not None:
                    slot = (slot + 1) % self.ring_size  # Linear probing
                    if slot == original_slot:
                        raise Exception("Hash ring is full.")
                self.ring[slot] = f"Node-{node_id}"  
                self.node_map[slot] = f"Node-{node_id}"

    def get_node_for_request(self, request_id):  
        slot = self.H(request_id)
        original_slot = slot
        while self.ring[slot] is None:
            slot = (slot + 1) % self.ring_size
            if slot == original_slot:
                return None
        return self.ring[slot]