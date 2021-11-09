import test_servers as ts
from drone.waypoint_manager import WaypointManager
from drone.system import System
from drone.connection import Connection
from drone.drone_connection import DroneConnection
from drone.window_manager import LocationWindowManager, TimeWindowManager
from common.headings import *
import numpy as np
from common.protocol import Protocol

import threading 

IP = "127.0.0.1"
SERVER_PORT = 9876
DRONE_PORT = 9875

# Server setup part

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

test_server = ts.TestServer(
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
    SERVER_PORT,
    period=.2
)
drone = ts.DroneServer(
    "Drone",
    1,
    0,
    1,
    IP,
    DRONE_PORT
)

ts_thread = threading.Thread(target=test_server.start)
drone_thread = threading.Thread(target=drone.start)

ts_thread.start()
drone_thread.start()

# System start part

connection = Connection(IP, SERVER_PORT)
dconn = DroneConnection(IP, DRONE_PORT)
lmng = LocationWindowManager()
tmng = TimeWindowManager()
wmng = WaypointManager()
desired_cps = 30

system = System(
    connection,
    dconn,
    lmng,
    tmng,
    wmng,
    desired_cps=desired_cps
)
system_thread = threading.Thread(target=system.run)
system_thread.start()



