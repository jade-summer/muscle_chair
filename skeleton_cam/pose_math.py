"""
Skeleton Camera - 姿勢計算ユーティリティ

カメラやMediaPipeに依存しない純粋な幾何計算をまとめたモジュール。
"""

import math


def calculate_angle(
    point_a: list[float], point_b: list[float], point_c: list[float]
) -> float:
    """3点の座標(x, y)から頂点point_bの角度を算出"""
    rad = math.atan2(point_c[1] - point_b[1], point_c[0] - point_b[0]) - math.atan2(
        point_a[1] - point_b[1], point_a[0] - point_b[0]
    )
    angle = abs(rad * 180.0 / math.pi)
    if angle > 180.0:
        angle = 360 - angle
    return round(angle, 1)
