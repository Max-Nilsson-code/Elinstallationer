#!/usr/bin/env python3
"""Läser käll-PDF:en och bygger fragor.json samt bilder/.

Körs bara när käll-PDF:en byts ut. Den löpande redigeringen sker i
fragor.json, som är facit för innehållet — inte den här filen.

    python3 verktyg/extrahera.py
"""
import json
import re
from pathlib import Path

import pypdf

ROT = Path(__file__).resolve().parent.parent
PDF = ROT / "Övningsuppgifter Montörshandbok och Faktabok.pdf"
JSON_UT = ROT / "fragor.json"
BILDKATALOG = ROT / "bilder"

# Punktlistor i PDF:en använder ett Symbol-typsnitt: tecknet hamnar i
# Unicodes private use area istället för som ett vanligt bullet.
BULLET = ""

# Vilka frågor som faktiskt kräver en figur går inte att avgöra maskinellt:
# "nedanstående" syftar oftast på en punktlista, medan fråga 199 ("den här
# dosdimmern") behöver sin bild utan att nämna ordet bild. Tabellen nedan är
# därför genomgången för hand mot PDF:en.
KRAVER_BILD = {
    "1": ["sida01-1.jpg", "sida01-2.jpg", "sida01-3.jpg", "sida01-4.jpg"],
    "9": ["sida02-1.jpg", "sida02-2.jpg", "sida02-3.jpg",
          "sida02-4.jpg", "sida02-5.jpg", "sida02-6.jpg"],
    # Ritningen över lunchrummet ligger sist i PDF:en men hör till dessa två.
    "44": ["sida51-1.jpg"],
    "36": ["sida06-1.jpg", "sida06-2.jpg"],
    "51": ["sida51-1.jpg"],
    "75": ["sida13-1.jpg", "sida13-2.jpg", "sida13-3.jpg",
           "sida13-4.jpg", "sida13-5.jpg"],
    "141": ["sida23-1.jpg"],
    "150": ["sida25-1.jpg"],
    "157": ["sida26-1.jpg"],
    "158": ["sida27-1.jpg", "sida28-1.jpg"],
    "178": ["sida31-1.jpg"],
    "189": ["sida33-1.png"],
    "199": ["sida35-1.jpg"],
    "202": ["sida37-1.jpg"],
    "210": ["sida39-1.jpg"],
}

# Bilder som bara illustrerar — frågan går att besvara utan dem.
ILLUSTRATIONER = {
    "sida37-2.jpg": "Foto av spabad (fråga 203)",
    "sida40-1.jpg": "Foto av solcellsanläggning (kapitel 15)",
}

# Material som frågorna hänvisar till men som inte följer med PDF:en.
SAKNAT_MATERIAL = {
    "B48": "Bilaga A saknas i PDF:en.",
}

# Används bara för att varna om en ny upplaga av PDF:en innehåller
# figurhänvisningar som ingen ännu har granskat.
BILDORD = re.compile(r"\b(figur|figurer|figurerna)\b|\bpå bilden\b|\bpå bilderna\b", re.I)

RUBRIK_FAKTA = re.compile(r"^Faktabok Kapitel\s+(.+?)\s*$")
RUBRIK_MONT = re.compile(r"^Montörshandbok Kapitel\s+(.+?)\s*$")
DEL_B_START = "Elinstallationsreglerna SS 436 40 00 är uppbyggd"
FRAGA = re.compile(r"^(\d+)\.\s*(.*)$")

# Fråga 73 är ett offert-case vars sju delfrågor har egen numrering 1–7.
CASE_FRAGA = 73


def stada(text: str) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    # PDF:en avstavar vid radbrytning ("E-\nnummer"), vilket annars ger "E- nummer".
    # Bindestrecket måste sitta ihop med ordet före, annars är det ett listtecken.
    return re.sub(r"(?<=\w)-\s+(?=\w)", "-", text)


def ar_svarsrad(rad: str) -> bool:
    """Ifyllnadsraderna i del B består enbart av punkter och mellanslag."""
    return bool(rad) and set(rad) <= set(".… ")


def las_sidor(pdf: pypdf.PdfReader):
    for nr, sida in enumerate(pdf.pages, start=1):
        yield nr, (sida.extract_text() or "").split("\n")


def parsa(pdf: pypdf.PdfReader) -> list[dict]:
    avsnitt: list[dict] = []
    aktuellt: dict | None = None
    fraga: dict | None = None
    i_del_b = False
    # Delfrågorna under case-frågan numreras om från 1, precis som del B.
    i_case = False

    def stang():
        nonlocal fraga
        if fraga is None:
            return
        fraga["text"] = stada(" ".join(fraga.pop("_rader")))
        if not fraga["punkter"]:
            del fraga["punkter"]
        aktuellt["fragor"].append(fraga)
        fraga = None

    for sidnr, rader in las_sidor(pdf):
        for rad in rader:
            s = rad.strip()
            if not s:
                continue

            if DEL_B_START in s:
                stang()
                i_del_b, i_case = True, False
                aktuellt = {
                    "del": "B",
                    "titel": "Elinstallationsreglerna SS 436 40 00",
                    "faktabok": None,
                    "montorshandbok": None,
                    "sida": sidnr,
                    "fragor": [],
                }
                avsnitt.append(aktuellt)
                continue

            if not i_del_b and (m := RUBRIK_FAKTA.match(s)):
                stang()
                i_case = False
                aktuellt = {
                    "del": "A",
                    "titel": f"Faktabok kapitel {m.group(1)}",
                    "faktabok": m.group(1),
                    "montorshandbok": None,
                    "sida": sidnr,
                    "fragor": [],
                }
                avsnitt.append(aktuellt)
                continue

            if not i_del_b and (m := RUBRIK_MONT.match(s)):
                stang()
                # Montörshandbok-rubriken hör till avsnittet ovanför.
                if aktuellt is not None and aktuellt["montorshandbok"] is None:
                    aktuellt["montorshandbok"] = m.group(1)
                    aktuellt["titel"] += f" + Montörshandbok kapitel {m.group(1)}"
                continue

            if aktuellt is None:
                continue  # försättsblad

            if m := FRAGA.match(s):
                nummer = int(m.group(1))
                # Numreringen börjar om inuti case-frågan; först när den når
                # 74 igen är vi tillbaka i den löpande serien.
                if i_case and nummer > 7:
                    i_case = False
                stang()
                if i_del_b:
                    ident, etikett = f"B{nummer}", f"B{nummer}"
                elif i_case:
                    ident = f"{CASE_FRAGA}.{nummer}"
                    etikett = ident
                else:
                    ident, etikett = str(nummer), str(nummer)
                    if nummer == CASE_FRAGA:
                        i_case = True
                fraga = {
                    "id": ident,
                    "nummer": etikett,
                    "sida": sidnr,
                    "_rader": [m.group(2)] if m.group(2) else [],
                    "punkter": [],
                    "kraver_bild": False,
                    "bilder": [],
                }
                continue

            if fraga is None or ar_svarsrad(s):
                continue
            if s.startswith(BULLET):
                fraga["punkter"].append(stada(s.lstrip(BULLET)))
            else:
                fraga["_rader"].append(s)

    stang()
    return avsnitt


def spara_bilder(pdf: pypdf.PdfReader) -> dict[int, list[str]]:
    """Skriver ut inbäddade bilder och returnerar filnamn per sidnummer."""
    BILDKATALOG.mkdir(exist_ok=True)
    for gammal in BILDKATALOG.glob("sida*"):
        gammal.unlink()

    per_sida: dict[int, list[str]] = {}
    for sidnr, sida in enumerate(pdf.pages, start=1):
        for i, bild in enumerate(sida.images, start=1):
            ändelse = Path(bild.name).suffix or ".png"
            namn = f"sida{sidnr:02d}-{i}{ändelse}"
            (BILDKATALOG / namn).write_bytes(bild.data)
            per_sida.setdefault(sidnr, []).append(namn)
    return per_sida


def markera_bilder(avsnitt: list[dict], per_sida: dict[int, list[str]]) -> None:
    """Kopplar figurer till frågor enligt den granskade tabellen."""
    filer = {namn for namnlista in per_sida.values() for namn in namnlista}
    kopplade: set[str] = set()

    for avs in avsnitt:
        for fraga in avs["fragor"]:
            if bilder := KRAVER_BILD.get(fraga["id"]):
                saknade = [b for b in bilder if b not in filer]
                if saknade:
                    raise SystemExit(
                        f"Fråga {fraga['id']} pekar på bilder som inte finns: {saknade}"
                    )
                fraga["kraver_bild"] = True
                fraga["bilder"] = bilder
                kopplade.update(bilder)
            if anm := SAKNAT_MATERIAL.get(fraga["id"]):
                fraga["anmarkning"] = anm
            if fraga["id"] not in KRAVER_BILD and BILDORD.search(fraga["text"]):
                print(f"  varning: fråga {fraga['id']} nämner en figur men saknas i "
                      f"KRAVER_BILD (s. {fraga['sida']})")

    # Varna hellre än att tappa bort en bild om PDF:en byts ut.
    okand = sorted(filer - kopplade - set(ILLUSTRATIONER))
    for namn in okand:
        print(f"  varning: {namn} är inte kopplad till någon fråga")


def main() -> None:
    if not PDF.exists():
        raise SystemExit(f"Hittar inte käll-PDF:en: {PDF}")
    pdf = pypdf.PdfReader(str(PDF))

    avsnitt = parsa(pdf)
    markera_bilder(avsnitt, spara_bilder(pdf))

    antal = sum(len(a["fragor"]) for a in avsnitt)
    JSON_UT.write_text(
        json.dumps(
            {
                "kalla": PDF.name,
                "antal_avsnitt": len(avsnitt),
                "antal_fragor": antal,
                "saknat_material": SAKNAT_MATERIAL,
                "illustrationer": ILLUSTRATIONER,
                "avsnitt": avsnitt,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"Skrev {JSON_UT.name}: {len(avsnitt)} avsnitt, {antal} frågor")


if __name__ == "__main__":
    main()
