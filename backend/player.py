import uuid

class Player:
    def __init__(self):
        self.ID: str = self.generateUUID()
        self.sock = None
    
    def generateUUID(self) -> str:
        # uuid4 is random
        return str(uuid.uuid4())

