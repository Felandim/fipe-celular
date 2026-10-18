import json, os, re, shutil, sys, tempfile, unittest
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import generate as g

CFG = {"site_name": "FIPE do Celular", "base_url": "https://x.pages.dev", "AMAZON_TAG": "felipelandas-20", "ML_AFFILIATE_ID": "NLLMSY-281S", "ml_matt_word": "lafe1562447", "ml_matt_tool": "17865852"}
OFFERS = [
    {"model": "iPhone 13", "storage": "128GB", "slug": "iphone-13-128gb", "condition": "Bom", "price": 2189.0},
    {"model": "iPhone 13", "storage": "128GB", "slug": "iphone-13-128gb", "condition": "Excelente", "price": 2449.0},
    {"model": "iPhone 13", "storage": "128GB", "slug": "iphone-13-128gb", "condition": "Muito Bom", "price": 2329.0},
]


class TestGenerate(unittest.TestCase):
    def setUp(self):
        self.e = g.group(OFFERS)["iphone-13-128gb"]
        self.html = g.model_page(self.e, {"iphone-13-128gb": [("2026-10-14", 2300.0), ("2026-10-15", 2329.0)]}, "2026-10-15", CFG)

    def test_stats(self):
        self.assertEqual(self.e["median"], 2329.0)
        self.assertEqual((self.e["min"], self.e["max"]), (2189.0, 2449.0))

    def test_title_canonical(self):
        self.assertIn("<title>iPhone 13 128GB usado: quanto vale hoje (tabela atualizada)</title>", self.html)
        self.assertIn('<link rel="canonical" href="https://x.pages.dev/iphone-13-128gb/">', self.html)
        self.assertIn('lang="pt-BR"', self.html)

    def test_disclaimer_and_date(self):
        self.assertIn("recondicionado na loja</strong>, não de venda entre particulares", self.html)
        self.assertIn("15 de outubro de 2026", self.html)

    def test_faq_jsonld(self):
        m = re.search(r'<script type="application/ld\+json">(.*?)</script>', self.html)
        d = json.loads(m.group(1))
        self.assertEqual(d["@type"], "FAQPage")
        self.assertEqual(len(d["mainEntity"]), 3)

    def test_affiliate_links(self):
        self.assertIn("tag=felipelandas-20", self.html)
        self.assertEqual(self.html.count('rel="sponsored nofollow noopener"'), 2)
        self.assertIn("matt_word=lafe1562447&amp;matt_tool=17865852", self.html)
        self.assertIn("comissão", self.html)

    def test_ml_with_id(self):
        self.assertEqual(g.ml_url("iPhone 13 128GB", CFG), "https://lista.mercadolivre.com.br/iphone-13-128gb?matt_word=lafe1562447&matt_tool=17865852")
        self.assertNotIn("matt", g.ml_url("x", dict(CFG, ml_matt_word="", ml_matt_tool="")))

    def test_chart(self):
        self.assertIn("<svg", self.html)
        self.assertIn("começa hoje", g.svg_chart([("2026-10-15", 1.0)]))

    def test_brl(self):
        self.assertEqual(g.brl(2189), "R$ 2.189,00")
        self.assertEqual(g.brl(1803.09), "R$ 1.803,09")

    def test_home_search(self):
        h = g.home(g.group(OFFERS), "2026-10-15", CFG)
        self.assertIn('id="q"', h)
        self.assertIn('href="/iphone-13-128gb/"', h)


if __name__ == "__main__":
    unittest.main()
