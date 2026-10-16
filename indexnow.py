#!/usr/bin/env python3
import json, os, re, urllib.request
ROOT = os.path.dirname(os.path.abspath(__file__))
c = json.load(open(os.path.join(ROOT, "config.json")))
urls = re.findall(r"<loc>([^<]+)</loc>", open(os.path.join(ROOT, "public", "sitemap.xml")).read())
host = c["base_url"].split("//")[1]
body = json.dumps({"host": host, "key": c["indexnow_key"], "keyLocation": f"{c['base_url']}/{c['indexnow_key']}.txt", "urlList": urls[:10000]}).encode()
req = urllib.request.Request("https://api.indexnow.org/indexnow", data=body, headers={"Content-Type": "application/json; charset=utf-8"})
try:
    with urllib.request.urlopen(req, timeout=30) as r:
        print("IndexNow", r.status, len(urls), "URLs")
except urllib.error.HTTPError as e:
    print("IndexNow HTTP", e.code, e.read()[:200])
