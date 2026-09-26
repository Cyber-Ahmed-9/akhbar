"""Text helpers: cleaning, language guess, tagging, clustering."""
import html
import re
import time

_TAG_RE = re.compile(r"<[^>]+>")
_WS = re.compile(r"\s+")
_AR = re.compile(r"[\u0600-\u06FF]")


def clean(s: str) -> str:
    return _WS.sub(" ", html.unescape(_TAG_RE.sub(" ", s or ""))).strip()


def is_arabic(s: str) -> bool:
    letters = [c for c in s if c.isalpha()]
    return bool(letters) and sum(1 for c in letters if _AR.match(c)) / len(letters) > 0.3


COUNTRIES = {
    "العراق": ["iraq", "baghdad", "erbil", "kurdistan", "basra", "العراق", "بغداد", "أربيل", "البصرة"],
    "إيران": ["iran", "tehran", "irgc", "khamenei", "إيران", "طهران", "الحرس الثوري", "خامنئي"],
    "إسرائيل": ["israel", "idf", "netanyahu", "إسرائيل", "الاحتلال", "نتنياهو"],
    "فلسطين": ["gaza", "hamas", "west bank", "palestin", "غزة", "حماس", "الضفة", "فلسطين"],
    "لبنان": ["lebanon", "hezbollah", "beirut", "لبنان", "حزب الله", "بيروت"],
    "سوريا": ["syria", "damascus", "سوريا", "دمشق"],
    "اليمن": ["yemen", "houthi", "اليمن", "الحوثي"],
    "الخليج": ["saudi", "riyadh", "emirat", "abu dhabi", "qatar", "doha", "kuwait", "bahrain", "oman",
               "السعودية", "الرياض", "الإمارات", "قطر", "الكويت", "البحرين", "عمان"],
    "أمريكا": ["u.s.", "united states", "washington", "white house", "pentagon", "trump", "congress",
               "أمريكا", "واشنطن", "البيت الأبيض", "البنتاغون", "ترامب"],
    "روسيا وأوكرانيا": ["russia", "moscow", "kremlin", "putin", "ukrain", "kyiv", "روسيا", "موسكو", "بوتين", "أوكرانيا"],
    "الصين": ["china", "beijing", "xi jinping", "taiwan", "الصين", "بكين", "تايوان"],
    "تركيا": ["turkey", "türkiye", "turkiye", "ankara", "erdogan", "تركيا", "أنقرة", "أردوغان"],
}
TOPICS = {
    "نووي": ["nuclear", "iaea", "uranium", "enrichment", "نووي", "تخصيب", "اليورانيوم", "الطاقة الذرية"],
    "عسكري": ["strike", "missile", "drone", "attack", "military", "troops", "airstrike",
              "ضربة", "صاروخ", "مسيرة", "هجوم", "عسكري", "غارة", "قصف"],
    "دبلوماسية": ["talks", "negotiat", "summit", "sanction", "ceasefire", "envoy",
                  "محادثات", "مفاوضات", "قمة", "عقوبات", "هدنة", "وقف إطلاق"],
    "نفط وطاقة": ["oil", "opec", "crude", "gas price", "energy", "نفط", "أوبك", "الغاز", "الطاقة"],
    "اقتصاد": ["economy", "inflation", "market", "tariff", "central bank", "اقتصاد", "تضخم", "أسواق", "البنك المركزي"],
    "سياسة داخلية": ["election", "parliament", "vote", "cabinet", "انتخابات", "البرلمان", "مجلس الوزراء"],
}
ALL_TAGS = list(COUNTRIES) + list(TOPICS)


def tags_for(text: str) -> str:
    low = (text or "").lower()
    return "|".join(k for k, kws in {**COUNTRIES, **TOPICS}.items() if any(w in low for w in kws))


_STOP = set("""the and for with from that this after over into amid says said will has have was were are its not but
new more about what how who why can could would than their they his her out off all one two news live updates report
reports latest video watch""".split()) | set("في من على إلى عن مع بعد قبل التي الذي هذا هذه حول خلال بين أن إن كان قال يقول تقرير عاجل".split())
_SPLIT = re.compile(r"[^\w]+", re.UNICODE)


def tokens(s: str) -> set:
    return {w for w in _SPLIT.split((s or "").lower()) if len(w) > 2 and w not in _STOP and not w.isdigit()}


def cluster(rows: list, window_h: int = 48) -> list:
    """Greedy clustering on English text (original or ar→en translation)."""
    cutoff = time.time() - window_h * 3600
    recent = sorted((r for r in rows if r["published"] > cutoff), key=lambda r: r["published"])
    groups, keys = [], []
    for r in recent:
        t = tokens(r.get("title_en") or r["title"])
        best, best_score = -1, 0.0
        if len(t) >= 3:
            for i, g in enumerate(keys):
                if len(g) < 3:
                    continue
                inter = len(t & g)
                if inter < 3:
                    continue
                score = inter / min(len(t), len(g))
                if score >= 0.5 and score > best_score:
                    best, best_score = i, score
        if best >= 0:
            groups[best].append(r)
        else:
            groups.append([r]); keys.append(t)
    events = []
    for g in groups:
        lead = min(g, key=lambda r: (r["tier"], r["published"]))
        events.append({
            "key": g[0]["id"],
            "tiers": sorted({r["tier"] for r in g}),
            "latest": max(r["published"] for r in g),
            "lead_id": lead["id"],
            "items": sorted(g, key=lambda r: (r["tier"], r["published"])),
        })
    events.sort(key=lambda e: e["latest"], reverse=True)
    return events
