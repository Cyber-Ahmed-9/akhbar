"""Seven-tier source registry (same as the Android app)."""
from urllib.parse import quote_plus

TIERS = [
    {"id": 1, "emoji": "🟦", "name": "الخبر العاجل", "short": "عاجل", "color": "#4A90D9"},
    {"id": 2, "emoji": "🟩", "name": "الصحافة السياسية الحصرية", "short": "حصري", "color": "#4CAF7A"},
    {"id": 3, "emoji": "🟨", "name": "الشبكات العالمية", "short": "عالمي", "color": "#E0B84A"},
    {"id": 4, "emoji": "🟥", "name": "الروايات الإقليمية", "short": "إقليمي", "color": "#D9594C"},
    {"id": 5, "emoji": "🟪", "name": "الوكالات الرسمية", "short": "وكالات", "color": "#9B6BD1"},
    {"id": 6, "emoji": "⬛", "name": "المصدر الأصلي", "short": "أصلي", "color": "#9AA0A8"},
    {"id": 7, "emoji": "🔎", "name": "التحقق", "short": "تحقق", "color": "#4FB3BF"},
]


def gn(q: str, ar: bool = False) -> str:
    """Google News RSS bridge for outlets without a public feed."""
    base = "https://news.google.com/rss/search?q=" + quote_plus(f"{q} when:2d")
    return base + ("&hl=ar&gl=IQ&ceid=IQ:ar" if ar else "&hl=en-US&gl=US&ceid=US:en")


def S(id, name, tier, url):
    return {"id": id, "name": name, "tier": tier, "url": url}


SOURCES = [
    S("reuters", "Reuters", 1, gn("site:reuters.com")),
    S("ap", "AP", 1, gn("site:apnews.com")),
    S("afp", "AFP", 1, gn('"AFP" OR site:afp.com')),
    S("bloomberg", "Bloomberg", 1, "https://feeds.bloomberg.com/politics/news.rss"),

    S("axios", "Axios", 2, "https://api.axios.com/feed/"),
    S("politico", "Politico", 2, "https://rss.politico.com/politics-news.xml"),
    S("punchbowl", "Punchbowl", 2, gn("site:punchbowl.news")),
    S("semafor", "Semafor", 2, gn("site:semafor.com")),
    S("puck", "Puck", 2, gn("site:puck.news")),
    S("notus", "NOTUS", 2, gn("site:notus.org")),
    S("thehill", "The Hill", 2, "https://thehill.com/feed/"),

    S("bbc", "BBC", 3, "https://feeds.bbci.co.uk/news/world/rss.xml"),
    S("cnn", "CNN", 3, gn("site:cnn.com")),
    S("sky", "Sky News", 3, "https://feeds.skynews.com/feeds/rss/world.xml"),
    S("france24", "France 24", 3, "https://www.france24.com/en/rss"),
    S("dw", "DW", 3, "https://rss.dw.com/rdf/rss-en-all"),
    S("aljazeera", "Al Jazeera", 3, "https://www.aljazeera.com/xml/rss/all.xml"),
    S("alarabiya", "Al Arabiya", 3, gn("site:english.alarabiya.net")),
    S("rt", "RT", 3, "https://www.rt.com/rss/news/"),
    S("cgtn", "CGTN", 3, gn("site:cgtn.com")),

    S("irna", "IRNA", 4, gn("site:en.irna.ir")),
    S("presstv", "Press TV", 4, gn("site:presstv.ir")),
    S("alalam", "Al-Alam", 4, gn("site:alalam.ir", ar=True)),
    S("fars", "Fars", 4, gn("site:farsnews.ir")),
    S("tasnim", "Tasnim", 4, gn("site:tasnimnews.com")),
    S("mehr", "Mehr", 4, "https://en.mehrnews.com/rss"),
    S("iranintl", "Iran International", 4, gn("site:iranintl.com")),
    S("almonitor", "Al-Monitor", 4, gn("site:al-monitor.com")),
    S("mee", "Middle East Eye", 4, "https://www.middleeasteye.net/rss"),
    S("toi", "Times of Israel", 4, "https://www.timesofisrael.com/feed/"),
    S("haaretz", "Haaretz", 4, gn("site:haaretz.com")),

    S("ina", "INA", 5, gn("site:ina.iq", ar=True)),
    S("spa", "SPA", 5, gn("site:spa.gov.sa", ar=True)),
    S("wam", "WAM", 5, gn("site:wam.ae", ar=True)),
    S("qna", "QNA", 5, gn("site:qna.org.qa", ar=True)),
    S("mena", "MENA", 5, gn("site:mena.org.eg", ar=True)),
    S("anadolu", "Anadolu", 5, "https://www.aa.com.tr/en/rss/default?cat=guncel"),
    S("tass", "TASS", 5, "https://tass.com/rss/v2.xml"),
    S("xinhua", "Xinhua", 5, gn("site:english.news.cn")),

    S("whitehouse", "White House", 6, gn("site:whitehouse.gov")),
    S("pentagon", "Pentagon", 6, gn("site:defense.gov")),
    S("state", "State Department", 6, gn("site:state.gov")),
    S("centcom", "CENTCOM", 6, gn("site:centcom.mil")),
    S("iranmfa", "Iranian MFA", 6, gn("site:mfa.ir")),
    S("irgc", "IRGC", 6, gn("IRGC statement")),
    S("idf", "IDF", 6, gn("site:idf.il")),
    S("iraqgov", "Iraqi Government", 6, gn("site:gov.iq", ar=True)),
    S("un", "UN", 6, "https://news.un.org/feed/subscribe/en/news/all/rss.xml"),
    S("iaea", "IAEA", 6, gn("site:iaea.org")),

    S("bellingcat", "Bellingcat", 7, "https://www.bellingcat.com/feed/"),
    S("bbcverify", "BBC Verify", 7, gn('"BBC Verify"')),
    S("reutersfc", "Reuters Fact Check", 7, gn("site:reuters.com/fact-check")),
    S("apfc", "AP Fact Check", 7, gn("site:apnews.com/ap-fact-check")),
    S("afpfc", "AFP Fact Check", 7, gn("site:factcheck.afp.com")),
]
SOURCE_BY_ID = {s["id"]: s for s in SOURCES}
