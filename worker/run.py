"""One update cycle, run by GitHub Actions:
fetch all sources -> store -> translate -> cluster -> ntfy alerts -> write the static site."""
import calendar
import json
import os
import shutil
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import feedparser
import httpx

sys.path.insert(0, str(Path(__file__).parent))
from sources import SOURCES, TIERS  # noqa: E402
from textproc import ALL_TAGS, clean, cluster, is_arabic, tags_for  # noqa: E402
from translator import Translator  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
STATE = ROOT / "state" / "state.json"
SITE = ROOT / "site"
MAX_TRANSLATE = int(os.environ.get("MAX_TRANSLATE", 250))   # per run, newest first
NTFY_TOPIC = os.environ.get("NTFY_TOPIC", "").strip()
REPO = os.environ.get("GITHUB_REPOSITORY", "")
UA = "Mozilla/5.0 (X11; Linux x86_64) AkhbarWorker/1.0"
NOW = time.time()


def log(*a):
    print(time.strftime("%H:%M:%S"), *a, flush=True)


def load_json(p, default):
    try:
        return json.loads(Path(p).read_text(encoding="utf-8"))
    except Exception:
        return default


cfg = {"keywords": "", "notify_urgent": True, "notify_confirmed": True, "retention_days": 3, "disabled_sources": []}
cfg.update(load_json(ROOT / "config.json", {}))
state = load_json(STATE, {"items": {}, "next_id": 1, "notified": [], "status": {}, "runs": 0})
first_run = not state["items"]
client = httpx.Client(timeout=20, follow_redirects=True, headers={"User-Agent": UA})


# ---------------- 1. fetch ----------------
def entry_time(e):
    for k in ("published_parsed", "updated_parsed"):
        if e.get(k):
            return min(float(calendar.timegm(e[k])), NOW)
    return NOW


def fetch(s):
    try:
        r = client.get(s["url"]); r.raise_for_status()
        feed = feedparser.parse(r.content)
        gn = "news.google.com" in s["url"]
        out = []
        for e in feed.entries[:50]:
            title, link = clean(e.get("title", "")), e.get("link", "")
            if not title or not link:
                continue
            if gn and " - " in title:
                title = title.rsplit(" - ", 1)[0]
            summary = "" if gn else clean(e.get("summary", ""))[:400]
            out.append({"source_id": s["id"], "source_name": s["name"], "tier": s["tier"], "title": title,
                        "summary": summary, "link": link, "published": entry_time(e),
                        "tags": tags_for(f"{title} {summary}")})
        state["status"][s["id"]] = {"ok": 1, "msg": "", "at": NOW, "n": len(out)}
        return out
    except Exception as ex:
        state["status"][s["id"]] = {"ok": 0, "msg": f"{type(ex).__name__}: {str(ex)[:80]}", "at": NOW, "n": 0}
        return []


off = set(cfg.get("disabled_sources") or [])
active = [s for s in SOURCES if s["id"] not in off]
with ThreadPoolExecutor(12) as ex:
    batches = list(ex.map(fetch, active))

min_t = NOW - int(cfg.get("retention_days", 3)) * 86400
items = state["items"]
new = []
for rows in batches:
    for r in rows:
        if r["published"] < min_t or r["link"] in items:
            continue
        r.update(id=state["next_id"], lang=None, title_ar=None, summary_ar=None, title_en=None, tr=0)
        state["next_id"] += 1
        items[r["link"]] = r
        new.append(r)
for k in [k for k, v in items.items() if v["published"] < min_t]:
    del items[k]
ok = sum(1 for s in active if state["status"].get(s["id"], {}).get("ok"))
log(f"sources ok {ok}/{len(active)}, new items {len(new)}, stored {len(items)}")

# ---------------- 2. translate ----------------
tr = Translator()
pending = sorted((v for v in items.values() if not v["tr"]), key=lambda v: v["published"], reverse=True)
done = 0
t0 = time.time()
for v in pending[:MAX_TRANSLATE]:
    if is_arabic(v["title"]):
        v["lang"] = "ar"
        v["title_en"] = tr.translate(v["title"], "ar", "en") if tr.has("ar", "en") else None
        v["tr"] = 1
    elif tr.ok:
        v["lang"] = "en"
        v["title_ar"] = tr.translate(v["title"], "en", "ar")
        v["summary_ar"] = tr.translate(v["summary"], "en", "ar") if v["summary"] else None
        v["title_en"] = v["title"]; v["tr"] = 1
    else:
        continue  # translator unavailable: keep pending, retry next run
    done += 1
still = sum(1 for v in items.values() if not v["tr"])
log(f"translated {done} in {time.time() - t0:.0f}s (translator ok={tr.ok} {tr.error}), pending {still}")

# ---------------- 3. cluster ----------------
rows = list(items.values())
events = cluster(rows)
log(f"events {len(events)}, multi-tier {sum(1 for e in events if len(e['tiers']) >= 2)}")

# ---------------- 4. alerts (ntfy) ----------------
def ntfy(title, message, click, tags, priority=3):
    if not NTFY_TOPIC:
        return
    try:
        client.post("https://ntfy.sh", json={"topic": NTFY_TOPIC, "title": title, "message": message,
                                             "click": click, "tags": tags, "priority": priority})
    except Exception as e:
        log("ntfy failed", e)


notified = set(state["notified"])
if first_run:
    # do not flood the phone on the very first run
    notified |= {f"ev{e['key']}" for e in events}
    log("first run: alerts skipped")
else:
    if cfg.get("notify_urgent", True):
        kws = [k.strip().lower() for k in str(cfg.get("keywords", "")).replace("،", ",").split(",") if k.strip()]
        hits = [r for r in new if r["tier"] == 1 and (not kws or any(k in r["title"].lower() for k in kws))]
        for r in hits[:5]:
            ntfy(f"عاجل · {r['source_name']}", r.get("title_ar") or r["title"], r["link"], ["rotating_light"], 4)
        log(f"urgent alerts {min(len(hits), 5)}")
    if cfg.get("notify_confirmed", True):
        sent = 0
        for e in events:
            k = f"ev{e['key']}"
            if len(e["tiers"]) < 3 or k in notified or sent >= 3:
                continue
            notified.add(k); sent += 1
            lead = next(i for i in e["items"] if i["id"] == e["lead_id"])
            names = "، ".join(dict.fromkeys(i["source_name"] for i in e["items"]))
            ntfy(f"حدث مؤكد من {len(e['tiers'])} مستويات", f"{lead.get('title_ar') or lead['title']}\n{names}",
                 lead["link"], ["white_check_mark"], 3)
        log(f"confirmed alerts {sent}")
live = {f"ev{e['key']}" for e in events}
state["notified"] = sorted(notified & live)[-2000:]

# ---------------- 5. write site ----------------
PUB = ("id", "source_id", "source_name", "tier", "title", "summary", "link", "published", "tags",
       "title_ar", "summary_ar", "lang")


def pub(v):
    return {k: v.get(k) for k in PUB}


if SITE.exists():
    shutil.rmtree(SITE)
shutil.copytree(ROOT / "web", SITE)
(SITE / "data").mkdir()
(SITE / ".nojekyll").write_text("")


def dump(name, obj):
    (SITE / "data" / name).write_text(json.dumps(obj, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")


ordered = sorted(rows, key=lambda v: v["published"], reverse=True)
dump("items.json", [pub(v) for v in ordered[:1500]])
dump("events.json", [{**{k: e[k] for k in ("key", "tiers", "latest", "lead_id")},
                      "items": [pub(i) for i in e["items"]]} for e in events[:300]])
per = {}
for v in rows:
    per[v["tier"]] = per.get(v["tier"], 0) + 1
state["runs"] += 1
dump("meta.json", {"tiers": TIERS, "tags": ALL_TAGS, "count": len(rows), "pending": still, "per_tier": per,
                   "updated": NOW, "new": len(new), "translator": tr.ok, "translator_error": tr.error,
                   "sources_ok": ok, "sources_active": len(active), "runs": state["runs"], "repo": REPO,
                   "config": {k: cfg[k] for k in ("keywords", "notify_urgent", "notify_confirmed", "retention_days")},
                   "ntfy": bool(NTFY_TOPIC)})
dump("sources.json", [{**s, "enabled": s["id"] not in off, "status": state["status"].get(s["id"])} for s in SOURCES])

STATE.parent.mkdir(parents=True, exist_ok=True)
STATE.write_text(json.dumps(state, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
log("site written:", SITE)
