import socket
import threading
import time
from typing import Optional, List
from .connection import Connection

"""
드론 관련해서 송수힌 하는 클래스
현재는 파라미터값과 드론 상태를 모두 tcp를 통해서 받아오기 때문에
connection의 코드를 재사용 함
"""

class DroneConnection(Connection):
    pass
