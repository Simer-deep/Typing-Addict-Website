import os
import tempfile
import unittest
from datetime import timedelta


TEST_DIRECTORY = tempfile.mkdtemp(prefix="typing-addict-tests-")
os.environ["DATABASE_URL"] = f"sqlite:///{os.path.join(TEST_DIRECTORY, 'test.sqlite3')}"

from app import app, utc_now  # noqa: E402
from models import GameControl, db  # noqa: E402


class LobbyFlowTest(unittest.TestCase):
    def setUp(self):
        app.config.update(TESTING=True)
        with app.app_context():
            db.drop_all()
            db.create_all()

    def register(self, client, username, display_name):
        response = client.post("/register", json={"username": username, "password": "password123"})
        self.assertEqual(response.status_code, 201)
        response = client.put("/me/profile", json={"display_name": display_name})
        self.assertEqual(response.status_code, 200)

    def test_waiting_room_host_transfer_and_three_rounds(self):
        host = app.test_client()
        player = app.test_client()
        self.register(host, "host-user", "Host Racer")
        self.register(player, "player-user", "Player Two")

        created = host.post(
            "/lobbies",
            json={"name": "Test room", "player_limit": 4, "viewer_limit": 2},
        )
        self.assertEqual(created.status_code, 201)
        lobby = created.get_json()
        code = lobby["code"]
        host_id = lobby["host_user_id"]

        joined = player.post(f"/lobbies/{code}/join", json={"role": "player"})
        self.assertEqual(joined.status_code, 200)
        player_id = next(row["user_id"] for row in joined.get_json()["players"] if row["name"] == "Player Two")

        roster = host.get(f"/lobbies/{code}").get_json()
        self.assertEqual({row["name"] for row in roster["players"]}, {"Host Racer", "Player Two"})
        self.assertEqual(player.post(f"/lobbies/{code}/start").status_code, 403)

        kicked = host.delete(f"/lobbies/{code}/players/{player_id}")
        self.assertEqual(kicked.status_code, 200)
        self.assertEqual(player.post(f"/lobbies/{code}/join", json={"role": "player"}).status_code, 200)

        left = host.delete(f"/lobbies/{code}/leave")
        self.assertEqual(left.status_code, 200)
        self.assertEqual(left.get_json()["host_user_id"], player_id)
        self.assertNotEqual(host_id, player_id)

        started = player.post(f"/lobbies/{code}/start")
        self.assertEqual(started.status_code, 201)
        self.assertEqual(started.get_json()["game_order"], ["typing", "clicking", "spacebar"])
        self.assertEqual(player.post(f"/lobbies/{code}/next").status_code, 409)

        with app.app_context():
            control = GameControl.query.one()
            control.phase = "running"
            control.round_started_at = utc_now() - timedelta(seconds=5)
            db.session.commit()
        typed = player.post(
            f"/lobbies/{code}/game/submit",
            json={"round_index": 0, "typed": started.get_json()["prompt"]},
        )
        self.assertEqual(typed.status_code, 201)
        typing_board = player.get(f"/lobbies/{code}/game").get_json()
        self.assertEqual(typing_board["phase"], "leaderboard")
        self.assertGreater(typing_board["standings"][0]["round_score"], 0)
        self.assertEqual(host.post(f"/lobbies/{code}/next").status_code, 403)
        next_round = player.post(f"/lobbies/{code}/next")
        self.assertEqual(next_round.status_code, 200)
        self.assertEqual(next_round.get_json()["round_index"], 1)

        with app.app_context():
            control = GameControl.query.one()
            control.phase = "running"
            control.round_started_at = utc_now() - timedelta(seconds=5)
            db.session.commit()
        clicked = player.post(
            f"/lobbies/{code}/game/submit",
            json={"round_index": 1, "count": 30},
        )
        self.assertEqual(clicked.status_code, 201)
        self.assertEqual(player.post(f"/lobbies/{code}/next").get_json()["round_index"], 2)

        with app.app_context():
            control = GameControl.query.one()
            control.phase = "running"
            control.round_started_at = utc_now() - timedelta(seconds=5)
            db.session.commit()
        spacebar = player.post(
            f"/lobbies/{code}/game/submit",
            json={"round_index": 2, "count": 35},
        )
        self.assertEqual(spacebar.status_code, 201)
        finished = player.post(f"/lobbies/{code}/next")
        self.assertEqual(finished.status_code, 200)
        self.assertEqual(finished.get_json()["phase"], "finished")


if __name__ == "__main__":
    unittest.main()
