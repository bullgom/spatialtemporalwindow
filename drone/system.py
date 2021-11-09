from typing import Tuple, List, Any, Optional
from .connection import Connection
from .drone_connection import DroneConnection
from .window_manager import LocationWindowManager, TimeWindowManager
from .waypoint_manager import WaypointManager
from .event_manager import EventManager
from common.protocol import Protocol
from common.headings import *
from enum import Enum, auto
import numpy as np
import datetime
import time
"""
메인 파일

전체 시스템 합친 부분
"""


class Events(Enum):
    MissionStart = auto()
    MissionFinished = auto()

    TakeOff = auto()
    Landing = auto()

    WaypointReached = auto()
    WaypointsReceived = auto()
    LWinParamReceived = auto()
    TWinParamReceived = auto()
    WMngParamReceived = auto()
    GPSReceived = auto()
    EmergencyLanding = auto()
    LocationCheckTime = auto()


class System:

    def __init__(
        self,
        connection: Connection,
        drone_connection: DroneConnection,
        location_manager: LocationWindowManager,
        time_manager: TimeWindowManager,
        waypoint_manager: WaypointManager,
        desired_cps: Optional[float] = 20,
    ) -> None:
        self.connection = connection
        self.drone_connection = drone_connection
        self.location_manager = location_manager
        self.time_manager = time_manager
        self.waypoint_manager = waypoint_manager
        self.event_manager = EventManager()
        self.protocol = Protocol()

        # How many cycles of receiving & processing per seconds
        self.desired_cps = desired_cps
        self.desired_time_per_cycle = 1/self.desired_cps

        self.current_position: Optional[np.ndarray] = None
        self.direction_vector: Optional[np.ndarray] = None
        self.mission_started = False

        events = [
            Events.MissionFinished,
            Events.MissionStart,
            Events.TakeOff,
            Events.Landing,
            Events.WaypointReached,
            Events.WaypointsReceived,
            Events.LWinParamReceived,
            Events.TWinParamReceived,
            Events.WMngParamReceived,
            Events.GPSReceived,
            Events.EmergencyLanding,
            Events.LocationCheckTime,
        ]
        for e in events:
            self.event_manager.register(e)

        self.setup()
        self.running = True

    def setup(self):
        """
        이벤트 callback 함수들 등록하기
        """
        self.event_manager.subscribe(
            Events.MissionStart, self.on_mission_start)
        self.event_manager.subscribe(
            Events.MissionFinished, self.on_mission_finished)

        self.event_manager.subscribe(Events.TakeOff, self.on_takeoff)
        self.event_manager.subscribe(Events.Landing, self.on_landing)

        self.event_manager.subscribe(
            Events.LWinParamReceived, self.on_l_win_param_received)
        self.event_manager.subscribe(
            Events.TWinParamReceived, self.on_t_win_param_received)
        self.event_manager.subscribe(
            Events.WMngParamReceived, self.on_w_mng_param_received)
        self.event_manager.subscribe(Events.GPSReceived, self.on_gps_received)
        self.event_manager.subscribe(
            Events.WaypointReached, self.on_waypoint_reached)
        self.event_manager.subscribe(
            Events.WaypointsReceived, self.on_waypoints_received)
        self.event_manager.subscribe(
            Events.LocationCheckTime, self.on_location_check_time)

    """이벤트 발생 부분"""

    def run(self):
        """
        프로토콜이 파싱한 데이터의 이름-> 함수로 매핑하고 실행
        """

        while self.running:
            start = datetime.datetime.now()

            if (encoded := self.connection.get()):
                data_list = self.protocol.decode(encoded)
                self.receive_from_connection(data_list)

            if (encoded := self.drone_connection.get()):
                data_list = self.protocol.decode(encoded)
                self.receive_from_drone(data_list)

            elapsed = (datetime.datetime.now() - start).total_seconds()
            
            if self.mission_started:
                if elapsed >= self.location_manager.check_period:
                    self.event_manager.publish(Events.LocationCheckTime, elapsed)

                if self.waypoint_manager.mission_finished():
                    self.event_manager.publish(Events.MissionFinished)
                else:
                    self.send_vector()

            elapsed = (datetime.datetime.now() - start).total_seconds()
            remaining = self.desired_time_per_cycle - elapsed

            if remaining < 0:
                print("Warning: System is running slower than desired cps")
            else:
                time.sleep(remaining)

    def receive_from_connection(self, data_list: List[Tuple[str, Any]]):
        for name, value in data_list:
            print(f"RP Received {name} from server")
            if name in L_WIN_PARAM_NAMES:
                self.event_manager.publish(
                    Events.LWinParamReceived, name, value)

            if name in T_WIN_PARAM_NAMES:
                self.event_manager.publish(
                    Events.TWinParamReceived, name, value)

            if name in WAYPOINT_PARAM_NAMES:
                self.event_manager.publish(
                    Events.WMngParamReceived, name, value)

            if name == WAYPOINTS:
                self.event_manager.publish(Events.WaypointsReceived, value)
            
            if name == TAKEOFF:
                self.event_manager.publish(Events.TakeOff)
            
            if name == MISSION_START:
                self.event_manager.publish(Events.MissionStart)

    def receive_from_drone(self, data_list: List[Tuple[str, Any]]):
        for name, value in data_list:
            print(f"RP Received {name} from drone")

            if name == GPS_POSITION:
                self.event_manager.publish(Events.GPSReceived, value)

    """이벤트 처리 부분"""

    def on_l_win_param_received(self, name: str, value: Any):
        print(f"Setting Location Window Parameter: {name} - {value}")
        setattr(self.location_manager, name, value)

    def on_t_win_param_received(self, name: str, value: Any):
        print(f"Setting Time Window Parameter: {name} - {value}")
        setattr(self.time_manager, name, value)

    def on_w_mng_param_received(self, name: str, value: Any):
        print(f"Setting Waypoint Parameter: {name} - {value}")
        setattr(self.waypoint_manager, name, value)

    def on_waypoints_received(self, encoded_waypoints: bytes):
        # decode string -> numpy array
        waypoints = self.protocol.decode_waypoints(encoded_waypoints)
        self.waypoint_manager.set_mission(waypoints)

    def on_gps_received(self, encoded_gps_position: bytes):
        gps_position = self.protocol.decode_point(encoded_gps_position)
        self.current_position = gps_position
        print(f"Current gps: {self.current_position}")

        if not self.mission_started:
            return
        
        if self.waypoint_manager.waypoint_reached(gps_position):
            self.event_manager.publish(Events.WaypointReached, gps_position)

    def on_waypoint_reached(self, gps: np.ndarray):
        print(f"Waypoint {self.waypoint_manager.current_waypoint()} reached")
        last_wp = self.waypoint_manager.last_waypoint()

        if not self.time_manager.in_range(gps, last_wp):
            self.event_manager.publish(Events.EmergencyLanding)
        self.time_manager.update_check_time()

        self.waypoint_manager.to_next_waypoint()

    def on_location_check_time(self, elapsed_time: float):

        if not self.location_manager.in_range(
            elapsed_time,
            self.current_position,
            self.waypoint_manager.last_waypoint(),
            self.direction_vector
        ):
            self.event_manager.publish(Events.EmergencyLanding)

    def on_mission_finished(self):
        self.event_manager.publish(Events.Landing)
        self.stop()

    def on_mission_start(self):
        self.mission_started = True
        self.waypoint_manager.start_mission()

    def on_takeoff(self):
        data = self.protocol.encode(1, TAKEOFF)
        self.drone_connection.send(data)

    def on_landing(self):
        data = self.protocol.encode(1, LAND)
        self.drone_connection.send(data)

    def on_emergency_landing(self):
        print("Emergency landing")
        data = self.protocol.encode(1, EMERGENCY_LANDING)
        self.drone_connection.send(data)
        self.stop()

    def send_vector(self):

        vec = self.waypoint_manager.waypoint2vector(
            self.waypoint_manager.current_waypoint(),
            self.current_position
        )
        self.direction_vector = vec

        data = self.protocol.encode(self.protocol.encode_point(vec), VECTOR)
        self.drone_connection.send(data)

        data = self.protocol.encode(
            self.waypoint_manager.desired_velocity, DESIRED_VELOCITY)
        self.drone_connection.send(data)

    def stop(self):
        self.drone_connection.clean()
        self.connection.clean()
        self.running = False
        