import pytest
from fastapi.testclient import TestClient

from backend import main


@pytest.fixture
def client(monkeypatch):
    sent_commands: list[tuple[str, str]] = []

    async def fake_send_command(device_name: str, url: str, winner: str) -> None:
        sent_commands.append((device_name, winner))

    monkeypatch.setattr(main, "_send_command", fake_send_command)
    monkeypatch.setitem(main.game_state, "team_a_gauge", 0.0)
    monkeypatch.setitem(main.game_state, "team_b_gauge", 0.0)
    monkeypatch.setitem(main.game_state, "last_win_time", 0.0)
    monkeypatch.setitem(main.game_state, "last_winner", None)

    with TestClient(main.app) as test_client:
        test_client.sent_commands = sent_commands
        yield test_client


def test_converts_known_source_by_its_weight():
    assert main.convert_to_point("pushup_sensor", 3) == 30.0


def test_converts_unknown_source_to_zero():
    assert main.convert_to_point("unknown_sensor", 100) == 0.0


def test_squat_and_pushup_are_both_scored():
    # client.py の SOURCE_BY_MODE が送る source と対応していること
    assert main.convert_to_point("squat_sensor", 1) > 0
    assert main.convert_to_point("pushup_sensor", 1) > 0


def test_serves_the_spectator_ui_at_the_root(client):
    response = client.get("/")

    assert response.status_code == 200
    assert "Muscle Chair" in response.text


def test_add_point_accumulates_into_the_reporting_team(client):
    client.post("/add_point", json={"source": "pushup_sensor", "value": 2, "team": "a"})

    assert main.game_state["team_a_gauge"] == 20.0
    assert main.game_state["team_b_gauge"] == 0.0


def test_add_point_rejects_unknown_team(client):
    response = client.post(
        "/add_point", json={"source": "pushup_sensor", "value": 1, "team": "c"}
    )

    assert response.status_code == 422


def test_add_point_rejects_non_positive_value(client):
    response = client.post(
        "/add_point", json={"source": "pushup_sensor", "value": 0, "team": "a"}
    )

    assert response.status_code == 422


def test_reaching_the_threshold_triggers_output_and_resets_gauges(client):
    for _ in range(main.WINNING_THRESHOLD // 10):
        client.post(
            "/add_point", json={"source": "pushup_sensor", "value": 1, "team": "a"}
        )

    assert client.sent_commands == [("single_device", "team_a")]
    assert main.game_state["team_a_gauge"] == 0.0
    assert main.game_state["last_winner"] == "team_a"


def test_no_second_victory_during_cooldown(client):
    def fill_team_a_to_threshold():
        for _ in range(main.WINNING_THRESHOLD // 10):
            client.post(
                "/add_point", json={"source": "pushup_sensor", "value": 1, "team": "a"}
            )

    fill_team_a_to_threshold()
    fill_team_a_to_threshold()

    assert len(client.sent_commands) == 1


def test_status_hides_the_winner_once_the_cooldown_expired(client, monkeypatch):
    monkeypatch.setitem(main.game_state, "last_winner", "team_a")
    monkeypatch.setitem(main.game_state, "last_win_time", 0.0)

    body = client.get("/status").json()

    assert body["is_cooldown"] is False
    assert body["last_winner"] is None
