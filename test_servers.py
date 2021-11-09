from typing import Optional, List, Tuple, Any
from server import Server
from datetime import datetime
from common.headings import *
import threading
import numpy as np


class TestServer(Server):

    def __init__(
        self,
        name: str,
        data: List[Tuple[str, Any]],
        host: str,
        port: Optional[int] = 22,
        period: Optional[float] = 1.,
    ) -> None:
        super().__init__(name, host, port=port)

        self.period = period
        self.data = data

    def start(self):
        super().start()
        conn, addr = self.socket.accept()
        elapsed = 0.

        with conn:
            print(f"Connected from {addr}")
            self.start_receiving(conn)

            while self.data and conn:
                start = datetime.now()

                elapsed += (datetime.now() - start).total_seconds()

                if elapsed >= self.period:
                    data = self.data.pop(0)
                    print(f"Server sending : {data[0]}")
                    byte_data = self.protocol.encode(data[1], data[0])
                    conn.sendall(byte_data)

                    elapsed = 0.

            self.clean()


class DroneServer(Server):

    def __init__(
        self,
        name,
        gps_period: float,
        mean: float,
        sigma: float,
        host: str,
        port: Optional[int] = 22
    ) -> None:
        super().__init__(name, host, port=port)

        self.gps_period = gps_period
        self.takeoff_state: bool = False
        self.velocity: float = 0.
        self.direction: np.ndarray = np.zeros((3,))

        self.position = np.zeros((3,))

        self.mean = mean
        self.sigma = sigma

    def start(self):
        super().start()

        conn, addr = self.socket.accept()
        elapsed = 0.

        with conn:
            print(f"Connected from {addr}")
            self.start_receiving(conn)

            while conn:
                start = datetime.now()
                encoded = self.get()
                if encoded:
                    data = self.protocol.decode(encoded)

                    for name, value in data:

                        if name == TAKEOFF:
                            self.takeoff_state = True
                            print("Taking Off")

                        if name == LAND:
                            self.takeoff_state = False
                            print("Landing")

                        if name == EMERGENCY_LANDING:
                            self.takeoff_state = False
                            print("Emergency Landing")

                        if name == VECTOR:
                            vec = self.protocol.decode_point(value)
                            self.direction = vec

                        if name == DESIRED_VELOCITY:
                            self.velocity = value

                step_elapsed = (datetime.now() - start).total_seconds()

                if self.takeoff_state:
                    self.move(step_elapsed)

                elapsed += step_elapsed
                if elapsed >= self.gps_period:
                    pos = self.randomize_gps(self.position)
                    pos = self.protocol.encode_point(pos)
                    byte_data = self.protocol.encode(pos, GPS_POSITION)
                    
                    if conn:
                        conn.sendall(byte_data)

                    elapsed = 0.
                    
            self.clean()

    def move(self, time: float):
        self.position += self.direction * self.velocity * time

    def randomize_gps(self, gps: np.ndarray) -> np.ndarray:
        return gps + np.random.normal(loc=self.mean, scale=self.sigma, size=(3,))


if __name__ == "__main__":
    from common.headings import *
    import numpy as np
    from common.protocol import Protocol

    IP = "127.0.0.1"
    DRONE = 9875
    CENTER = 9876

    t_protocol = Protocol()

    waypoints = np.array(
        [
            [0., 0., 10.],
            [10., 10., 10.],
            [30., 10., 10.],
            [30., -10., 10.],
            [10., -10., 10.],
            [0., 0., 10.]
        ]
    )
    waypoints = t_protocol.encode_waypoints(waypoints)

    test_server = TestServer(
        "Center",
        [
            (WAYPOINTS, waypoints),
            (DESIRED_VELOCITY, 10.),
            (WINDOW_SIZE, 10.),
            (LOW_OFFSET, 5.),
            (HIGH_OFFSET, 5.),
            (COMMON_ERROR, 1.),
            (CHECK_PERIOD, 1.),
            (WAYPOINT_RANGE, 5.),
            (TAKEOFF, 1),
            (MISSION_START, 1)
        ],
        IP,
        CENTER,
        period=.3
    )
    drone = DroneServer(
        "Drone",
        1,
        0,
        1,
        IP,
        DRONE
    )

    ts_thread = threading.Thread(target=test_server.start)
    drone_thread = threading.Thread(target=drone.start)

    ts_thread.start()
    drone_thread.start()
