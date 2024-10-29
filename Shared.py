import threading

class Shared:
    def __init__(self, agent_name : str):
        self.agent_name=agent_name
        self.seq = 0
        self.ack = 0
        self.lock = threading.RLock()

    def get_seq(self) -> int:
        try:
            self.lock.acquire()
            return self.seq
        finally:
            self.seq += 1
            self.lock.release()

    def get_ack(self) -> int:
        try:
            self.lock.acquire()
            return self.ack
        finally:
            self.lock.release()
    
    def inc_ack(self) -> int:
        try:
            self.lock.acquire()
            self.ack += 1
        finally:
            self.lock.release()