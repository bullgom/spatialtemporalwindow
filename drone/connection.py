import socket
import threading
import time
from typing import Optional, List

class Connection:
    
    def __init__(self, host:str, port: Optional[int] = 22) -> None:
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
        connected = False
        while not connected:
            try:
                self.socket.connect((host, port))
                connected = True
            except ConnectionRefusedError:
                pass
        
        self.host = host
        self.port = port
        self.received_data : List[str] = []
        
        self.lock = threading.Lock()
        
        self.receiving = True
        self.receiving_thread = threading.Thread(target=self.receive)
        self.receiving_thread.start()
    
    def receive(self):
        while self.receiving:
            try:
                data = self.socket.recv(1024)
            except ConnectionResetError:
                self.receiving = False
                
            if data:
                with self.lock:
                    self.received_data.append(data)
            time.sleep(.5)
    
    def get(self) -> Optional[bytes]:
        data = None
        with self.lock:
            if self.received_data:
                data = self.received_data.pop(0)
        return data
    
    def send(self, x: bytes):
        self.socket.sendall(x)
    
    def clean(self):
        self.receiving = False
        self.receiving_thread.join()
        self.socket.close()
    
if __name__ == "__main__":
    
    connection = Connection('127.0.0.1', 2222)
    connection.send(b"Hi")
    print(connection.get())
    connection.clean()
