#!/usr/bin/env python3.10
import multiprocessing
import multiprocessing.managers
import multiprocessing.queues
import multiprocessing.synchronize
from typing import Tuple,Dict,Union,Any
from abc import ABC, abstractmethod


class Base_process(ABC,multiprocessing.Process):
    __processes_notifications: Dict[str, multiprocessing.synchronize.Condition]=None
    __processes_events: Dict[str, multiprocessing.synchronize.Event]=None
    __processes_data:Union[Dict[str,multiprocessing.queues.Queue],Dict[str,Dict[str,multiprocessing.queues.Queue]],Dict[str,multiprocessing.managers.ListProxy],Dict[str,Any],Dict[str,set]] =None
    stop_process = False
    getData_access_locker=multiprocessing.Lock()
    saveData_access_locker=multiprocessing.Lock()
    def __init__(self,process_name: str,process_arg: Tuple=None):
        self.process_name=process_name
        super().__init__(target=self.run,name=process_name,args=process_arg if process_arg != None else tuple())
    def Start_process(self):
        super().start()

    def Stop_process(self):
        self.stop_process=True
    
    def Join_process(self):
        super().join()
        
    @abstractmethod
    def run(self,*process_arg):
        pass 
    
    
    @property
    def processes_data(self):
        return self.__processes_data
    @processes_data.getter
    def processes_data(self):
        return self.__processes_data
    
    @processes_data.setter
    def processes_events(self,_processes_data):
        self.__processes_events=_processes_data
    
    @property
    def processes_events(self):
        return self.__processes_events
    @processes_events.getter
    def processes_events(self):
        return self.__processes_events
    @processes_events.setter
    def processes_events(self,_processes_events):
        self.__processes_events=_processes_events
    

    @classmethod
    def set_sherd_variables(cls,sherd_process_data:dict,sherd_process_notification:dict,sherd_process_data_evens:dict):
        cls.__processes_notifications=sherd_process_notification
        cls.__processes_events=sherd_process_data_evens
        cls.__processes_data=sherd_process_data 

    # Getter and setter methods for processes_data
    @classmethod
    def get_processes_data(cls,data_name:str)->Union[dict,multiprocessing.queues.Queue]:
        with cls.getData_access_locker:
            if(isinstance(cls.__processes_data[data_name],multiprocessing.queues.Queue)):
                if not cls.__processes_data[data_name].empty():
                    return cls.__processes_data[data_name].get()
                else:
                    return None
            else:
                return cls.__processes_data[data_name]
    @classmethod
    def save_processes_data(cls, data_name: str, data_value:Any):
        with cls.saveData_access_locker:
            if data_name not in cls.__processes_data.keys():
                raise ValueError(f"{data_name} not found. Ensure it's initialized.")
            if(isinstance(cls.__processes_data[data_name],dict) or isinstance(cls.__processes_data[data_name],multiprocessing.managers.DictProxy) ):
                cls.__processes_data[data_name].update(data_value)
            elif(isinstance(cls.__processes_data[data_name],list) or isinstance(cls.__processes_data[data_name],multiprocessing.managers.ListProxy) ):
                cls.__processes_data[data_name]=(data_value)
            elif(isinstance(cls.__processes_data[data_name],set)):
                cls.__processes_data[data_name]=(data_value)
            else:
                cls.__processes_data[data_name].put(data_value)

    # Getter and setter methods for processes_events
    @classmethod
    def get_processes_events(cls,event_name:str) ->  multiprocessing.synchronize.Event:
        return cls.__processes_events[event_name]

    @classmethod
    def create_processes_events(cls, event_name: str):
        if event_name not in cls.__processes_events.keys():
            cls.__processes_events[event_name] = multiprocessing.synchronize.Event()

    # Getter and setter methods for processes_notifications
    @classmethod
    def get_processes_notifications(cls,notify_name:str) -> multiprocessing.synchronize.Condition:
        return cls.__processes_notifications[notify_name]

    @classmethod
    def create_processes_notifications(cls, notification_name: str):
        if notification_name not in cls.__processes_notifications.keys():
            cls.__processes_notifications[notification_name] = multiprocessing.synchronize.Condition()