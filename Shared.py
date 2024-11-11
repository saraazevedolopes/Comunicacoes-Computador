import threading

class Shared:
    def __init__(self):
        self.seq = 3
        self.ack = 0
        self.lock = threading.RLock()

    def print(self):
        print(f"Dados deste agente: seq={self.seq}, ack={self.ack}")

    def acquire_lock(self):
        self.lock.acquire()

    def release_lock(self):
        self.lock.release()

    def get_seq(self) -> int:
        return self.seq

    def inc_seq(self, increment : int) -> int:
        self.seq += increment
        return self.seq
        
    def get_ack(self) -> int:
        return self.ack
       
    def inc_ack(self) -> int:
        self.ack += 1
        return self.ack
        