import threading

class Data:
    def __init__(self):
        self.agent_data : dict = dict()
        self.lock = threading.RLock()
        self.tasks = dict()

    def add_task(self, task_id, task_type):
        self.lock.acquire()

        if task_type == 3:
            self.tasks[int(task_id)] = [[],[],[]]
        else:
            self.tasks[int(task_id)] = []

        self.lock.release()
            
        print(f"TASK ID {task_id} com tipo {task_type}")
        
    def acquire_lock(self):
        self.lock.acquire()

    def release_lock(self):
        self.lock.release()