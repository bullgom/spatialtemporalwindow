from typing import Callable, Dict, List, Any


class EventManager:

    def __init__(self):
        self.subsciptions: Dict[Any, List[Callable]] = {}

    def register(self, event_name: Any):
        """새로운 event를 추가"""
        if event_name in self.subsciptions:
            raise ValueError(f"{event_name} is already registered")
        self.subsciptions[event_name] = []

    def subscribe(self, event_name: Any, function: Callable):
        """
        이벤트 event_name이 발생했을 때 function이 실행되도록 추가
        """
        if event_name not in self.subsciptions:
            raise KeyError(f"{event_name} is not registered")
        self.subsciptions[event_name].append(function)

    def publish(self, event_name: Any, *data):
        """
        이벤트 event_name이 발생했을 때
        구독 함수들을 data 값을 인자로 실행
        """
        if event_name not in self.subsciptions:
            raise KeyError(f"{event_name} is not registered")

        for f in self.subsciptions[event_name]:
            f(*data)
