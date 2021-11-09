from common.protocol import Protocol
from typing import Optional
import socket
import threading
import time


class Server:

    def __init__(self, name:str, host: str, port: Optional[int] = 22) -> None:
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        self.name = name
        self.host = host
        self.port = port

        self.protocol = Protocol()
        self.running = False

        self.received_data = []

        self.lock = threading.Lock()

        self.receiving = False

    def start_receiving(self, connection):
        self.receiving = True
        self.receiving_thread = threading.Thread(
            target=self.receive, args=(connection,))
        self.receiving_thread.start()

    def receive(self, connection):
        print(f"{self.name} started receiving")
        try:
            while self.receiving:
                try:
                    data = connection.recv(1024)
                except ConnectionResetError:
                    self.receiving = False
                    
                if data:
                    with self.lock:
                        self.received_data.append(data)
        except ConnectionAbortedError:
            pass
        print(f"{self.name} stopped receiving")

    def get(self) -> Optional[bytes]:
        data = None
        with self.lock:
            if self.received_data:
                data = self.received_data.pop(0)
        return data

    def start(self):
        self.socket.bind((self.host, self.port))
        self.socket.listen(5)
        self.running = True

    def clean(self):
        print(f"{self.name} cleaning")
        self.receiving = False
        self.running = False
        print(f"{self.name} closing socket")
        self.socket.close()
