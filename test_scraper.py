import unittest
from unittest.mock import Mock, patch

import requests
from bs4 import BeautifulSoup

import scraper


BOOKING_HTML = """
<form class="olbForm"><table class="single-select"><tbody>
<tr><td><input type="radio"></td><td>Type</td><td>Container No.</td><td>Status</td><td>Date</td><td>Place</td></tr>
<tr><td><input type="radio"></td><td>22GP</td><td>HLBU  2959982</td><td>Vessel arrived</td><td>2026-10-21</td><td>MANZANILLO</td></tr>
</tbody></table></form>
"""
DETAIL_HTML = """
<table class="groupBorder"><tr><td><table><tr><td>Type</td><td>22GP</td></tr></table></td></tr></table>
<table class="hl-tbl"><tbody><tr><td>Loaded</td><td>QINGDAO</td><td>2026-09-06</td><td>18:11</td><td>VESSEL</td><td>2633E</td></tr></tbody></table>
"""


class ScraperLiveBLTests(unittest.TestCase):
    @patch("scraper.get_zenrows_soup")
    def test_scrape_bl_uses_requested_bl_and_gets_container_details(self, get_soup):
        get_soup.side_effect = [
            BeautifulSoup(BOOKING_HTML, "html.parser"),
            BeautifulSoup(DETAIL_HTML, "html.parser"),
        ]

        result = scraper.scrape_bl("HLCUNG12608BMJY0", "test-key")

        self.assertEqual(result["bl_number"], "HLCUNG12608BMJY0")
        self.assertEqual(result["total_containers"], 1)
        self.assertEqual(result["containers"][0]["detailed_movements"][0]["status"], "Loaded")
        self.assertIn("blno=HLCUNG12608BMJY0", get_soup.call_args_list[0].args[0])

    def test_scrape_bl_requires_zenrows_key(self):
        with self.assertRaises(scraper.MissingZenRowsKey):
            scraper.scrape_bl("HLCUNG12608BMJY0", "")

    @patch("scraper.get_zenrows_soup")
    def test_scrape_bl_returns_zero_for_recognized_empty_results_table(self, get_soup):
        get_soup.return_value = BeautifulSoup('<form class="olbForm"><table class="single-select"><tbody></tbody></table></form>', "html.parser")

        result = scraper.scrape_bl("HLCUNG12608BMJY0", "test-key")

        self.assertEqual(result["total_containers"], 0)
        self.assertEqual(result["containers"], [])

    @patch("scraper.get_zenrows_soup")
    def test_scrape_bl_rejects_unrecognized_upstream_html(self, get_soup):
        get_soup.return_value = BeautifulSoup("<html><body>Unexpected challenge</body></html>", "html.parser")

        with self.assertRaises(scraper.ZenRowsError):
            scraper.scrape_bl("HLCUNG12608BMJY0", "test-key")

    @patch("scraper.requests.get")
    def test_scrape_bl_raises_for_zenrows_failure(self, get_request):
        response = Mock()
        response.raise_for_status.side_effect = requests.HTTPError("upstream unavailable")
        get_request.return_value = response

        with self.assertRaises(scraper.ZenRowsError):
            scraper.scrape_bl("HLCUNG12608BMJY0", "test-key")


if __name__ == "__main__":
    unittest.main()
