"""Download Argos en->ar and ar->en models (skipped if already cached)."""
import argostranslate.package as p

have = {(x.from_code, x.to_code) for x in p.get_installed_packages()}
need = [pair for pair in (("en", "ar"), ("ar", "en")) if pair not in have]
if not need:
    print("models already installed"); raise SystemExit
p.update_package_index()
avail = p.get_available_packages()
for a, b in need:
    pkg = next((x for x in avail if x.from_code == a and x.to_code == b), None)
    print(("installing" if pkg else "NOT FOUND"), a, "->", b)
    if pkg:
        p.install_from_path(pkg.download())
