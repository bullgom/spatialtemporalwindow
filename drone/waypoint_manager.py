from typing import List, Optional, Tuple
import numpy as np

"""
1. 웨이포인트 목록 관리
2. 다음 웨이포인트까지 가기 위한 벡터 계산
"""


class WaypointManager:

    def __init__(self, waypoint_range: Optional[float] = None) -> None:
        self.waypoints: Optional[np.ndarray] = None
        self.current_waypoint_index: Optional[int] = None
        self.waypoint_range = waypoint_range
        self.desired_velocity: Optional[float] = None

    def set_mission(self, waypoints: np.ndarray):
        """
        0번쨰 waypoint는 항상 시작 지점으로 세팅해야 함
        """
        self.waypoints = waypoints

    def start_mission(self):
        self.current_waypoint_index = 1
    
    def mission_finished(self) -> bool:
        return self.current_waypoint_index >= self.waypoints.shape[0]

    def waypoint_reached(self, current_pos: np.ndarray) -> bool:
        """
        현재 위치와 다음 웨이포인트 사이 거리를 계산하여, 범위 내에 있으면 도달한 것으로 판단한다.
        """
        d = np.linalg.norm(
            current_pos - self.waypoints[self.current_waypoint_index])

        return abs(d) <= self.waypoint_range

    def to_next_waypoint(self):
        self.current_waypoint_index += 1

    def waypoint2vector(
        self,
        waypoint: np.ndarray,
        current_pos: np.ndarray
    ) -> np.ndarray:
        diff = (waypoint - current_pos)
        direction = diff / np.linalg.norm(diff)

        return direction

    def current_waypoint(self) -> np.ndarray:
        return self.waypoints[self.current_waypoint_index]

    def last_waypoint(self) -> np.ndarray:
        return self.waypoints[self.current_waypoint_index-1]
