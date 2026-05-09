import shutil
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

import app.main as main


class RuntimeRouteTests(unittest.TestCase):
    def setUp(self):
        main.request_queue.clear()
        self.client = TestClient(main.app)

    def tearDown(self):
        main.request_queue.clear()
        data_dir = Path(main.BASE_DIR) / "data"
        if data_dir.exists():
            shutil.rmtree(data_dir)

    def test_passenger_page_renders_on_fresh_install(self):
        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        self.assertIn("Backseat DJ", response.text)
        self.assertIn("Add a song", response.text)

    def test_admin_page_renders_without_pin_when_unconfigured(self):
        response = self.client.get("/admin")

        self.assertEqual(response.status_code, 200)
        self.assertIn("Backseat DJ Admin", response.text)
        self.assertIn("Driver actions", response.text)

    def test_song_request_renders_confirmation_and_updates_health(self):
        response = self.client.post(
            "/request",
            data={"song": "Dreams", "artist": "Fleetwood Mac"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("Added", response.text)
        self.assertIn("Dreams", response.text)
        self.assertIn("Fleetwood Mac", response.text)
        health = self.client.get("/health").json()
        self.assertEqual(health["queue_length"], 1)


if __name__ == "__main__":
    unittest.main()
