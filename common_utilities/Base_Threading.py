#!/usr/bin/env python3.10
from typing import Tuple,Dict
from abc import ABC, abstractmethod
import threading
from queue import Queue




class Base_Thread(ABC):
    threads_events: Dict[str, threading.Event]=dict()
    threads_notifications: Dict[str, threading.Condition]=dict()
    threads_data: Dict[str, Queue] = dict()
    
    def __init__(self,thread_name: str,thread_arg: Tuple =()):
        self.thread_name=thread_name
        self.stop_thread = False
        self.thread=threading.Thread(target=self.run,name=self.thread_name,args=thread_arg)
        self.thread_started = False
    
    def Start_thread(self):
        self.thread.start()
        
    def Stop_thread(self):
        self.stop_thread=True
    
    def Join_thread(self):
        self.thread.join()

    def is_started(self):
        """
        Check if the thread is alive.
        
        Returns:
            bool: True if the thread is alive, False otherwise.
        """
        return self.thread_started
    @abstractmethod
    def run(self):  
        pass 