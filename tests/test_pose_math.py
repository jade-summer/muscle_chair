import pytest

from skeleton_cam.pose_math import calculate_angle


@pytest.mark.parametrize(
    ("point_a", "point_b", "point_c", "expected"),
    [
        ([0.0, 0.0], [1.0, 0.0], [2.0, 0.0], 180.0),
        ([0.0, 0.0], [0.0, 1.0], [1.0, 1.0], 90.0),
        ([1.0, 0.0], [0.0, 0.0], [0.0, 1.0], 90.0),
        ([2.0, 0.0], [1.0, 0.0], [0.0, 1.0], 135.0),
    ],
)
def test_returns_interior_angle_at_vertex(point_a, point_b, point_c, expected):
    assert calculate_angle(point_a, point_b, point_c) == expected


def test_result_never_exceeds_180_degrees():
    # 反射角（180度超）が算出されても劣角に折り返されること
    assert calculate_angle([1.0, 0.0], [0.0, 0.0], [-1.0, -0.001]) <= 180.0


def test_is_symmetric_in_outer_points():
    point_a, point_b, point_c = [0.0, 0.0], [1.0, 1.0], [2.0, 0.5]
    assert calculate_angle(point_a, point_b, point_c) == calculate_angle(
        point_c, point_b, point_a
    )
