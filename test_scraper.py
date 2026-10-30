import unittest
from unittest.mock import patch

from bs4 import BeautifulSoup

import scraper


BOOKING_HTML = """
<form>
  <table id="tracing_by_booking_f:hl27">
    <thead><tr><th></th><th>Type</th><th>Container No.</th><th>Status</th><th>Date</th><th>Place of Activity</th></tr></thead>
    <tbody>
      <tr><td><input type="radio" value="0"></td><td>22GP</td><td>HLBU  2959982</td><td>Vessel arrived</td><td>2026-10-21</td><td>MANZANILLO, COL (MX)</td></tr>
      <tr><td><input type="radio" value="1"></td><td>22GP</td><td>FTAU  1546275</td><td>Vessel arrived</td><td>2026-10-21</td><td>MANZANILLO, COL (MX)</td></tr>
    </tbody>
  </table>
</form>
"""

DETAIL_HTML = """
<table class="groupBorder"><thead><tr><th>Container Information</th></tr></thead><tbody>
<tr><td><table><tr><td>Type</td><td><span class="nonEditableContent">22GP</span></td></tr>
<tr><td>Description</td><td><span class="nonEditableContent">GENERAL PURPOSE CONT.</span></td></tr></table></td></tr></tbody></table>
<table class="hl-tbl"><thead><tr><th>Status</th><th>Place of Activity</th><th>Date</th><th>Time</th><th>Transport</th><th>Voyage No.</th></tr></thead>
<tbody><tr><td>Loaded</td><td>QINGDAO</td><td>2026-09-06</td><td>18:11</td><td>POSORJA EXPRESS</td><td>2633E</td></tr></tbody></table>
"""


class ScraperTests(unittest.TestCase):
    @patch("scraper.get_zenrows_soup")
    def test_scrapes_all_booking_containers_and_each_details_page(self, get_soup):
        get_soup.side_effect = [
            BeautifulSoup(BOOKING_HTML, "html.parser"),
            BeautifulSoup(DETAIL_HTML, "html.parser"),
            BeautifulSoup(DETAIL_HTML, "html.parser"),
        ]

        result = scraper.scrape_with_zenrows()

        self.assertEqual(result["total_containers"], 2)
        self.assertEqual([c["container_no"] for c in result["containers"]], ["HLBU 2959982", "FTAU 1546275"])
        self.assertEqual(result["containers"][0]["detailed_movements"][0]["status"], "Loaded")
        self.assertEqual(result["containers"][0]["container_information"]["Description"], "GENERAL PURPOSE CONT.")
        self.assertIn("view", get_soup.call_args_list[1].args[0])
        self.assertIn("container=HLBU++2959982", get_soup.call_args_list[1].args[0])


if __name__ == "__main__":
    unittest.main()
