"""Argos Translate wrapper (en<->ar), degrades gracefully if models are missing."""
import logging
import threading

log = logging.getLogger("akhbar.tr")


class Translator:
    def __init__(self):
        self.ok = False
        self.error = ""
        self._lock = threading.Lock()
        self._tr = {}
        try:
            import argostranslate.translate as at
            langs = {l.code: l for l in at.get_installed_languages()}
            for a, b in (("en", "ar"), ("ar", "en")):
                if a in langs and b in langs:
                    t = langs[a].get_translation(langs[b])
                    if t:
                        self._tr[(a, b)] = t
            self.ok = ("en", "ar") in self._tr
            if not self.ok:
                self.error = "نموذج en→ar غير مثبت"
        except Exception as e:  # pragma: no cover
            self.error = f"{type(e).__name__}: {e}"
        log.info("translator ok=%s pairs=%s %s", self.ok, list(self._tr), self.error)

    def has(self, a, b):
        return (a, b) in self._tr

    def translate(self, text: str, a: str, b: str):
        if not text or (a, b) not in self._tr:
            return None
        with self._lock:
            try:
                return self._tr[(a, b)].translate(text)
            except Exception as e:
                log.warning("translate failed: %s", e)
                return None
