import numpy as np
from typing import List, Optional
from datetime import datetime

class LocationWindowManager:

    def __init__(
        self,
        desired_velocity: Optional[float] = None,
        window_size: Optional[float] = None,
        check_period: Optional[float] = None
    ):
        self.desired_velocity = desired_velocity
        self.window_size = window_size
        self.check_period = check_period

    def in_range(
        self,
        elapsed_time: float,
        current_position: np.ndarray,
        start_waypoint: np.ndarray,
        direction_vector: np.ndarray
    ) -> bool:
        """
        주기마다 실행
        """
        E_travel_distance = elapsed_time * self.desired_velocity
        E_location = start_waypoint + (direction_vector * E_travel_distance)
        return np.linalg.norm(current_position - E_location) <= self.window_size


class TimeWindowManager:

    def __init__(
        self,
        desired_velocity: Optional[float] = None,
        low_offset: Optional[float] = None,
        high_offset: Optional[float] = None,
        common_error: Optional[float] = None
    ):
        self.desired_velocity = desired_velocity
        self.low_offset = low_offset
        self.high_offset = high_offset
        self.common_error = common_error
        
        self.last_check_time = datetime.now()

    def in_range(
        self,
        current_pos: np.ndarray,
        last_waypoint: np.ndarray
    ) -> bool:
        """
        waypoint 도달마다 실행
        기대 경과 시간
        """
        
        elapsed_time = (datetime.now() - self.last_check_time).total_seconds()
        
        d = abs(np.linalg.norm(last_waypoint - current_pos))
        E_time = d/self.desired_velocity
        low = E_time * self.low_offset - self.common_error
        high = E_time * self.high_offset + self.common_error

        return low <= elapsed_time <= high

    def update_check_time(self):
        self.last_check_time = datetime.now()
