from typing import Optional, Tuple, Any, List
import numpy as np

"""
역할
1. bytes 값을 받아서 파싱
2. 해당 값을 

Protocol
#이름-값[-타입]

타입은 선택적으로 보내며, default: float로 파싱이 된다.

예시
#desired_speed-12#low_offset-32#high_offset-123#some_string-hi-string
"""

Name = str


class Protocol:

    VALUE_TOKEN = "#"
    INTER_VALUE_TOKEN = "@"

    def __init__(self) -> None:
        self.str2type_map = {
            "int": int,
            "float": float,
            "str": str,
            "bytes": bytes
        }
        self.type2str_map = {v: k for k, v in self.str2type_map.items()}

    def decode(self, x: bytes, encoding: Optional[str] = "utf-8") -> List[Tuple[str, Any]]:
        values: List[Tuple[Name, Any]] = []

        string = x.decode(encoding=encoding)
        for entry in string.split(Protocol.VALUE_TOKEN)[1:]:
            splitted = entry.split(Protocol.INTER_VALUE_TOKEN)
            splitted.append("float")  # 있으면 해당 값으로 타입 사용, 없으면 float

            name = splitted[0]  # 이름
            type_ = self.str2type_map[splitted[2]]  # 타입
            value = type_(splitted[1])
            values.append((name, value))

        return values

    def encode(self, x: Any, name: Name) -> bytes:
        res = f"#{name}{self.INTER_VALUE_TOKEN}{Name(x)}{self.INTER_VALUE_TOKEN}{self.type2str_map[type(x)]}"
        return res.encode("utf-8")

    def encode_multiple(self, xs: List[Tuple[Any, Name]]) -> bytes:
        return "".join([self.encode(value, name) for value, name in xs])

    def encode_point(self, array: np.ndarray) -> str:
        """
        입력 (3,)
        출력 str
        """
        return np.array2string(array)

    def decode_point(self, data: str) -> np.ndarray:
        data = data.replace('[', '').replace(']', '')
        array = np.fromstring(data, dtype=float, sep=' ')
        return array

    def encode_waypoints(self, array: np.ndarray) -> str:
        """
        입력 (n, 3) 크기의 array 
        출력 str   
        """
        return self.encode_point(array)

    def decode_waypoints(self, data: str) -> np.ndarray:
        flattened = self.decode_point(data)
        return np.reshape(flattened, (-1, 3))
