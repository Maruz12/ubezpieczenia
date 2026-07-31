"""
Buduje fonty strony z pełnych plików źródłowych (fonts-src/) do fonts/.

Pliki z Google Fonts to fonty zmienne z pełną osią grubości i tysiącami glifów
dla wielu alfabetów. Strona jest po polsku i używa ~200 znaków, więc reszta to
balast na łączu komórkowym. Skrypt:

  1. zawęża oś grubości do faktycznie używanych wag,
  2. wycina wszystkie glify poza łaciną + polskimi znakami + typografią,
  3. zapisuje jako woff2.

Efekt: łacina i latin-ext lądują w JEDNYM pliku na krój, więc zamiast sześciu
żądań mamy trzy — i wszystkie można sensownie wrzucić w <link rel="preload">.

Uruchom ponownie tylko po podmianie plików w fonts-src/.
Wymaga: pip install fonttools brotli

UWAGA: na serwer wgrywasz TYLKO katalog fonts/ (3 pliki .woff2 + OFL.txt).
Katalog fonts-src/ i ten skrypt to narzędzia budowania — zostają lokalnie.

Licencja: Inter i Playfair Display są na SIL Open Font License 1.1,
która wprost dopuszcza hosting u siebie (patrz fonts/OFL.txt).
"""
import os
from fontTools import subset
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer

BASE = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.join(BASE, "fonts-src")
OUT_DIR = os.path.join(BASE, "fonts")

# Łacina podstawowa + Latin-1 + polskie znaki diakrytyczne + typografia
UNICODES = []
UNICODES += list(range(0x0020, 0x007F))   # ASCII
UNICODES += list(range(0x00A0, 0x0100))   # Latin-1 (ó, ä, ©, °, «»)
UNICODES += [                              # polskie znaki spoza Latin-1
    0x0104, 0x0105,  # Ą ą
    0x0106, 0x0107,  # Ć ć
    0x0118, 0x0119,  # Ę ę
    0x0141, 0x0142,  # Ł ł
    0x0143, 0x0144,  # Ń ń
    0x015A, 0x015B,  # Ś ś
    0x0179, 0x017A,  # Ź ź
    0x017B, 0x017C,  # Ż ż
]
UNICODES += [
    0x2013, 0x2014,  # – —
    0x2018, 0x2019, 0x201A,
    0x201C, 0x201D, 0x201E,
    0x2022, 0x2026,  # • …
    0x20AC, 0x2122,  # € ™
    0x2605,          # ★ (oceny)
]

# (plik źródłowy, plik wyjściowy, zawężenie osi)
JOBS = [
    ("Inter.ttf",           "inter.woff2",         {"wght": (400, 700), "opsz": 14}),
    ("Playfair.ttf",        "playfair.woff2",      {"wght": (600, 700)}),
    ("Playfair-Italic.ttf", "playfair-it.woff2",   {"wght": (600, 600)}),
]


def build(src_name, out_name, axis_limits):
    src = os.path.join(SRC_DIR, src_name)
    out = os.path.join(OUT_DIR, out_name)
    before = os.path.getsize(src)

    font = TTFont(src)

    if "fvar" in font:
        font = instancer.instantiateVariableFont(font, axis_limits, updateFontNames=False)
        # Po zawężeniu osi tabela gvar bywa bez wpisów dla części glifów,
        # na czym wywraca się subsetter. Uzupełniamy pustą listą wariacji.
        if "gvar" in font:
            gvar = font["gvar"]
            for glyph in font.getGlyphOrder():
                if glyph not in gvar.variations:
                    gvar.variations[glyph] = []

    options = subset.Options()
    options.flavor = "woff2"
    options.layout_features = ["kern", "liga", "clig", "calt", "ccmp", "locl", "mark", "mkmk"]
    options.name_IDs = ["*"]
    options.notdef_outline = True
    options.recalc_bounds = True

    subsetter = subset.Subsetter(options=options)
    subsetter.populate(unicodes=UNICODES)
    subsetter.subset(font)

    font.flavor = "woff2"
    font.save(out)
    after = os.path.getsize(out)
    print(f"{src_name:22s} -> {out_name:20s} {before/1024:7.1f} KB -> {after/1024:6.1f} KB "
          f"({100 - after / before * 100:4.1f}% mniej)")
    return after


os.makedirs(OUT_DIR, exist_ok=True)
for old in os.listdir(OUT_DIR):
    if old.endswith(".woff2"):
        os.remove(os.path.join(OUT_DIR, old))

total = sum(build(*job) for job in JOBS)
print("-" * 72)
print(f"{'RAZEM (pobiera przegladarka)':45s} {total/1024:6.1f} KB")
