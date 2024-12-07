import threading
from datetime import datetime

class Shared:
    def __init__(self, address : tuple=None):
        self.seq = 0
        self.ack = 0
        self.lock = threading.RLock()
        self.received_condition = threading.Condition(lock=self.lock)
        self.repeated_acks = 0
        self.received_ack = False
        self.received_packet = False
        self.ack_lock = threading.RLock()
        self.packets_received = set()
        self.address = address

    def acquire_lock(self):
        self.lock.acquire()

    def release_lock(self):
        self.lock.release()

    def acquire_ack_condition(self):
        self.ack_condition.wait()

    def notify_ack_condition(self):
        self.ack_condition.notifyAll()
    
    def received_seq(self, seq : int) -> bool:
        return seq in self.packets_received
    
    def add_packet(self, seq : int):
        self.packets_received.add(seq)

    def acquire_received_condition(self, seq : int, agent_logger) -> bool: # false -> timeout
        timestamp = datetime.now()
        difference = 0
        success = True
        try:
            self.lock.acquire()
            while (self.ack <= seq and difference < 2) and self.repeated_acks < 3: #or (self.repeated_acks < 3 and self.ack == seq): #and seq != 0): timeout = 2s
                self.received_condition.wait()
                difference = (datetime.now() - timestamp).total_seconds()
                
            if self.repeated_acks == 3:
                self.repeated_acks = 0
                agent_logger.warning(f"3 duplicated ACKs with {seq}")
                success = False
            elif difference > 2:
                success = False
                agent_logger.warning(f"TIMEOUT while sending packet with seq={seq}")

            return success
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