from enum import Enum

class Message_type(Enum):
    REGISTER = 0
    ACK = 1
    TASK = 2
    METRIC = 3
    END = 4
