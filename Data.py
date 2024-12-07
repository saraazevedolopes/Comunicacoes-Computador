import threading
from datetime import datetime

tasks = ["CPU", "RAM", "LATENCY", "IPERF", "INTERFACE"]

class Data:
    def __init__(self):
        #self.agent_data : dict = dict()
        self.lock = threading.RLock()
        self.tasks = list()

    def add_alert(self, task_id, task_type, metric):
        try:
            self.lock.acquire()
            metric = self.format_metrics(task_type, metric)
            self.tasks[task_id][2].append((datetime.now().strftime("%Y-%m-%d %H:%M:%S"),metric))
        finally:
            self.lock.release()

    def format_metrics(self, task_type, metric):
        if task_type in [0,1]:
            result=str(metric)+"%"
        elif task_type == 2:
            result=str(metric)+"ms"
        elif task_type == 3:
            if metric[0] == -1:
                result=metric[1]
            elif (metric[0] == 0 and metric[2] == 0):
                result="DESTINATION UNREACHABLE"
            elif len(metric) == 4:
                result=str(metric[0])+metric[1]+"bps "+str(metric[2])+"ms "+str(metric[3])+"%"
            else:
                result=str(metric[0])+"Mbps "+str(metric[1])+"ms "+str(metric[2])+"%"
        else:
            if metric == 0:
                result="DOWN"
            else:
                result="UP"
        return result
    
    def add_task(self, task_id, task_type, threshold, task_title):
        
        threshold = self.format_metrics(task_type, threshold)

        self.lock.acquire()
        while len(self.tasks) <= task_id:
            self.tasks.append(None)
        
        self.tasks[task_id] = (task_title,[],[], threshold)
        self.lock.release()
            
    def add_metrics(self, task_id, metric, task_type):
        metric = self.format_metrics(task_type,metric)
        self.lock.acquire()
        self.tasks[int(task_id)][1].append((datetime.now().strftime("%Y-%m-%d %H:%M:%S"),metric))
        self.lock.release()

    def get_metrics(self):
        try:
            self.lock.acquire()
            return [
                (
                    index,
                    task[0],  # Task type
                    [(metric[0], metric[1]) for metric in task[1]] if task[1] else [],  # NetTask metrics
                    [(alert[0], task[3], alert[1]) for alert in task[2]] if task[2] else []  # AlertFlow data
                )
                for index, task in enumerate(self.tasks)
            ]
        finally:
            self.lock.release()

    def acquire_lock(self):
        self.lock.acquire()

    def release_lock(self):
        self.lock.release()