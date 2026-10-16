import os, sys, unittest
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import collector as c
FIX = os.path.join(os.path.dirname(__file__), "fixture_small.html")


class TestCollector(unittest.TestCase):
    def test_parse_fixture(self):
        o = c.parse_product_html(open(FIX).read(), "https://www.trocafone.com.br/iphone-13-128gb/p")
        self.assertTrue(o)
        self.assertTrue(all(x["slug"] == "iphone-13-128gb" for x in o))
        self.assertTrue(all(x["price"] > 1000 for x in o))
        self.assertTrue({x["condition"] for x in o} <= {"Excelente", "Muito Bom", "Bom", "Outlet", "Novo"})

    def test_parse_garbage(self):
        self.assertEqual(c.parse_product_html("<html></html>"), [])
        self.assertEqual(c.parse_product_html(None), [])
        self.assertEqual(c.parse_product_html('data-varname="__STATE__"> <script>{bad</script>'), [])

    def test_normalize(self):
        self.assertEqual(c.normalize_model("Samsung Galaxy S23 128 GB Verde - Bom"), ("Galaxy S23", "128GB"))
        self.assertEqual(c.normalize_model("Iphone 13 Pro 128 GB Verde - Excelente"), ("iPhone 13 Pro", "128GB"))
        self.assertEqual(c.normalize_model("Samsung Galaxy S23 FE 128GB"), ("Galaxy S23 FE", "128GB"))
        self.assertEqual(c.normalize_model("iPhone 15 Pro Max 1TB"), ("iPhone 15 Pro Max", "1TB"))
        self.assertEqual(c.normalize_model("Capa sem armazenamento"), (None, None))

    def test_condition(self):
        self.assertEqual(c.condition_of("Azul Muito Bom"), "Muito Bom")
        self.assertEqual(c.condition_of("Rosa Bom"), "Bom")
        self.assertEqual(c.condition_of("Preto - Outlet"), "Outlet")
        self.assertIsNone(c.condition_of("Azul"))

    def test_url_filter(self):
        self.assertTrue(c.is_phone_url("https://www.trocafone.com.br/iphone-13-128gb/p"))
        self.assertTrue(c.is_phone_url("https://www.trocafone.com.br/samsung-galaxy-s23-128-gb-verde---bom-93517/p"))
        self.assertFalse(c.is_phone_url("https://www.trocafone.com.br/pelicula-dual-glass-para-iphone-13---preto---gshield-59074/p"))
        self.assertFalse(c.is_phone_url("https://www.trocafone.com.br/capa-clip-para-samsung-galaxy-s20---gshield-59202/p"))
        self.assertFalse(c.is_phone_url("https://www.trocafone.com.br/galaxy-fit-2-preto-bom/p"))

    def test_never_uses_search_api(self):
        src = open(c.__file__).read()
        self.assertNotIn("?ft=", src.replace('"?ft="', ""))
        self.assertNotIn("catalog_system", src)

    def test_robots_respected(self):
        import urllib.robotparser
        rp = urllib.robotparser.RobotFileParser()
        rp.parse(["User-agent: *", "Disallow: /busca/*", "Disallow: /*?ft=*"])
        self.assertTrue(rp.can_fetch(c.UA, "https://www.trocafone.com.br/iphone-13-128gb/p"))

    def test_sitemap_urls(self):
        self.assertEqual(c.sitemap_urls("<urlset><url><loc>https://a/p</loc></url></urlset>"), ["https://a/p"])


if __name__ == "__main__":
    unittest.main()
