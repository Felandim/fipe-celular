#!/usr/bin/env python3
"""Lê o Cloudflare Web Analytics (GraphQL, dataset rumPageloadEventsAdaptiveGroups) de um host.
Uso: cf-analytics.py <host> [dias=30] [--log arquivo.md]
Credenciais: /home/box/precifica-state/cloudflare.json (token com Account Analytics Read)."""
import json, sys, datetime, urllib.request
SEARCH = ("google.", "bing.", "duckduckgo.", "yahoo.", "yandex.", "ecosia.", "brave.", "search.")
args = [a for a in sys.argv[1:]]
log = None
if "--log" in args:
    i = args.index("--log"); log = args[i + 1]; del args[i:i + 2]
host = args[0]; days = int(args[1]) if len(args) > 1 else 30
c = json.load(open("/home/box/precifica-state/cloudflare.json"))
now = datetime.datetime.now(datetime.timezone.utc)
since = (now - datetime.timedelta(days=days)).strftime("%Y-%m-%dT%H:%M:%SZ")
until = now.strftime("%Y-%m-%dT%H:%M:%SZ")
q = """query($acc:String!,$f:AccountRumPageloadEventsAdaptiveGroupsFilter_InputObject){viewer{accounts(filter:{accountTag:$acc}){
 total:rumPageloadEventsAdaptiveGroups(limit:1,filter:$f){count sum{visits}}
 paths:rumPageloadEventsAdaptiveGroups(limit:15,filter:$f,orderBy:[count_DESC]){count dimensions{requestPath}}
 refs:rumPageloadEventsAdaptiveGroups(limit:15,filter:$f,orderBy:[count_DESC]){count dimensions{refererHost}}
 countries:rumPageloadEventsAdaptiveGroups(limit:10,filter:$f,orderBy:[count_DESC]){count dimensions{countryName}}}}}"""
v = {"acc": c["CLOUDFLARE_ACCOUNT_ID"], "f": {"AND": [{"datetime_geq": since, "datetime_leq": until}, {"requestHost": host}]}}
req = urllib.request.Request("https://api.cloudflare.com/client/v4/graphql", data=json.dumps({"query": q, "variables": v}).encode(),
                             headers={"Authorization": "Bearer " + c["CLOUDFLARE_API_TOKEN"], "Content-Type": "application/json"})
d = json.load(urllib.request.urlopen(req, timeout=30))
if d.get("errors"):
    sys.exit("GraphQL erro: " + json.dumps(d["errors"])[:400])
a = d["data"]["viewer"]["accounts"][0]
t = a["total"][0] if a["total"] else {"count": 0, "sum": {"visits": 0}}
paths = [(x["dimensions"]["requestPath"], x["count"]) for x in a["paths"]]
refs = [(x["dimensions"]["refererHost"] or "Direct", x["count"]) for x in a["refs"]]
ctry = [(x["dimensions"]["countryName"], x["count"]) for x in a["countries"]]
search = sum(n for h, n in refs if any(s in h for s in SEARCH))
stamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
line = (f"{stamp} BRT · {host} · {days}d: pageviews={t['count']} visits={t['sum']['visits']} busca={search} · "
        f"paths={paths[:8]} · referrers={refs[:8]} · países={ctry[:5]}")
print(line)
if log:
    with open(log, "a", encoding="utf-8") as fh:
        fh.write("\n" + line + "\n")
