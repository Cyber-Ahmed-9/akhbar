# رصد الأخبار (Akhbar) — GitHub edition

Free news monitor: GitHub Actions fetches, translates and groups the news every
15 minutes, and GitHub Pages hosts the Arabic web page.

Full beginner setup steps are in the chat message that came with this file.

Files:
- `web/` — the web page (index.html, icon, offline support)
- `worker/` — the Python script that runs on every update
- `.github/workflows/update.yml` — tells GitHub how to run the update
- `config.json` — your settings (edit this on GitHub)

config.json fields:
- `keywords` — breaking-news alert words, comma separated. Empty = all tier-1 news.
- `notify_urgent` / `notify_confirmed` — true or false.
- `retention_days` — how many days of news to keep.
- `disabled_sources` — list of source ids to skip, e.g. ["rt", "cgtn"].
