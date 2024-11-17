import threading
from datetime import datetime

class Shared:
    def __init__(self):
        self.seq = 0
        self.ack = 0
        self.lock = threading.RLock()
        self.received_condition = threading.Condition(lock=self.lock)
        self.repeated_acks = 0
        self.received_ack = False
        self.received_packet = False
        self.ack_lock = threading.RLock()

    def print(self):
        print(f"Dados deste agente: seq={self.seq}, ack={self.ack}")

    def acquire_lock(self):
        self.lock.acquire()

    def release_lock(self):
        self.lock.release()

    def acquire_ack_condition(self):
        self.ack_condition.wait()

    def notify_ack_condition(self):
        self.ack_condition.notifyAll()
    
    def acquire_received_condition(self, seq : int) -> bool: # false -> timeout
        timestamp = datetime.now()
        difference = 0

        try:
            self.lock.acquire()
            while self.ack < seq and difference < 5 : # timeout = 5s
                self.received_condition.wait()
                difference = (datetime.now() - timestamp).total_seconds()
                print(f"A difference é {difference}")

            print(f"Saí do loop e a diferença é {difference}")
            return difference < 5
        finally:
            self.lock.release()

    def notify_received_condition(self):
        self.lock.acquire()
        self.received_condition.notifyAll()
        self.lock.release()

    def get_received_packet(self) -> bool:
        try:
            self.lock.acquire()
            return self.received_packet
        finally:
            self.lock.release()

    def set_received_packet(self, value : bool):
        try:
            self.lock.acquire()
            self.received_packet = value
        finally:
            self.lock.release()

    def get_seq(self) -> int:
        return self.seq

    def inc_seq(self, increment : int) -> int:
        self.seq += increment
        return self.seq
        
    def get_ack(self) -> int:
        return self.ack
       
    def set_ack(self, ack : int):
        self.ack = ack
        self.repeated_acks = 0

    def inc_repeats(self):
        self.repeated_acks += 1

    def set_received_ack(self, state : bool):
        try:
            self.ack_lock.acquire()
            self.received_ack = state        
        finally:
            self.ack_lock.release()

    def get_received_ack(self) -> bool:
        try:
            self.ack_lock.acquire()
            return self.received_ack       
        finally:
            self.ack_lock.release()