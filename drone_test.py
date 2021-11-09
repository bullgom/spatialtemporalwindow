from drone.waypoint_manager import WaypointManager
from drone.system import System
from drone.connection import Connection
from drone.drone_connection import DroneConnection
from drone.window_manager import LocationWindowManager, TimeWindowManager


IP = "127.0.0.1"
SERVER_PORT = 9876
DRONE_PORT = 9875

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

system.run()
