import os, sys, unittest
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import generate


class BeaconTest(unittest.TestCase):
    def test_empty_token_no_script(self):
        self.assertEqual(generate.beacon_html(""), "")

    def test_token_in_script(self):
        h = generate.beacon_html("abc123")
        self.assertIn("static.cloudflareinsights.com/beacon.min.js", h)
        self.assertIn('"token": "abc123"', h)


if __name__ == "__main__":
    unittest.main()
