import importlib
import os
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient


class LiveTrackingRouteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.admin_token_patch = patch.dict(os.environ, {"ADMIN_TOKEN": "test-admin-token"})
        cls.admin_token_patch.start()
        import main
        cls.main = importlib.reload(main)
        cls.client = TestClient(cls.main.app)

    @classmethod
    def tearDownClass(cls):
        cls.admin_token_patch.stop()

    @patch("main.scraper.scrape_bl")
    def test_route_returns_live_results_for_requested_bl_each_time(self, scrape_bl):
        scrape_bl.side_effect = [
            {"bl_number": "HLCUNG12607EKZE0", "total_containers": 1, "containers": [{"container_no": "HLBU 2959982"}]},
            {"bl_number": "HLCUNG12608BMJY0", "total_containers": 2, "containers": []},
        ]

        first = self.client.get("/track/HLCUNG12607EKZE0")
        second = self.client.get("/track/HLCUNG12608BMJY0")

        self.assertEqual(first.status_code, 200)
        self.assertEqual(first.json()["total_containers"], 1)
        self.assertEqual(second.status_code, 200)
        self.assertEqual(second.json()["bl_number"], "HLCUNG12608BMJY0")
        self.assertEqual(scrape_bl.call_args_list[1].args[0], "HLCUNG12608BMJY0")

    def test_route_rejects_invalid_bl_before_scraping(self):
        with patch("main.scraper.scrape_bl") as scrape_bl:
            response = self.client.get("/track/invalid%20bl")

        self.assertEqual(response.status_code, 400)
        scrape_bl.assert_not_called()

    def test_route_reports_missing_zenrows_key(self):
        import main

        with patch.object(main.scraper, "scrape_bl", side_effect=main.scraper.MissingZenRowsKey("missing")):
            response = self.client.get("/track/HLCUNG12608BMJY0")

        self.assertEqual(response.status_code, 503)

    def test_route_reports_zenrows_upstream_failure(self):
        import main

        with patch.object(main.scraper, "scrape_bl", side_effect=main.scraper.ZenRowsError("upstream unavailable")):
            response = self.client.get("/track/HLCUNG12608BMJY0")

        self.assertEqual(response.status_code, 502)


if __name__ == "__main__":
    unittest.main()
