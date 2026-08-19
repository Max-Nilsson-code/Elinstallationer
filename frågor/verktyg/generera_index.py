#!/usr/bin/env python3
"""Genererar INDEX.md ur fragor.json.

fragor.json är facit. Rätta fel i frågetexten där och kör om det här
skriptet — ändringar direkt i INDEX.md skrivs över.

    python3 verktyg/generera_index.py
"""
import json
from pathlib import Path

ROT = Path(__file__).resolve().parent.parent
JSON_IN = ROT / "fragor.json"
MD_UT = ROT / "INDEX.md"

INGRESS = """# Övningsuppgifter — Elinstallation

Index över övningsuppgifterna till *Faktabok* och *Montörshandbok* för kursen
Elinstallation. Frågorna behåller sin numrering från käll-PDF:en, så att
"fråga 142" betyder samma sak här som i original och i klassrummet.

| | |
|---|---|
| Källa | [`{kalla}`]({kalla_lank}) |
| Antal frågor | {antal} |
| Del A | Fråga 1–219, grupperade per kapitel. Fråga 73 är ett offert-case med sju delfrågor (73.1–73.7). |
| Del B | Fråga B1–B53 om Elinstallationsreglerna SS 436 40 00. |

> Filen är genererad. Ändra i `fragor.json` och kör `python3 verktyg/generera_index.py`.
"""


def ankare(titel: str) -> str:
    """GitHubs egen regel för rubrikankare."""
    tecken = [t.lower() for t in titel if t.isalnum() or t in " -_"]
    return "#" + "".join(tecken).strip().replace(" ", "-")


def skriv_fraga(rader: list[str], fraga: dict) -> None:
    rader.append(f"#### {fraga['nummer']}. {fraga['text']}")
    rader.append("")
    for punkt in fraga.get("punkter", []):
        rader.append(f"- {punkt}")
    if fraga.get("punkter"):
        rader.append("")
    for bild in fraga["bilder"]:
        rader.append(f"![Figur till fråga {fraga['nummer']}](bilder/{bild})")
        rader.append("")
    if anmarkning := fraga.get("anmarkning"):
        rader.append(f"> **Obs:** {anmarkning}")
        rader.append("")
    rader.append(f"<sub>s. {fraga['sida']} i PDF:en</sub>")
    rader.append("")


def main() -> None:
    data = json.loads(JSON_IN.read_text(encoding="utf-8"))
    kalla = data["kalla"]
    rader = [
        INGRESS.format(
            kalla=kalla,
            kalla_lank=kalla.replace(" ", "%20"),
            antal=data["antal_fragor"],
        ),
        "## Innehåll",
        "",
    ]

    for avs in data["avsnitt"]:
        nummer = [f["nummer"] for f in avs["fragor"]]
        spann = f"{nummer[0]}–{nummer[-1]}" if len(nummer) > 1 else nummer[0]
        rader.append(
            f"- [{avs['titel']}]({ankare(avs['titel'])}) — "
            f"fråga {spann} ({len(nummer)} st), s. {avs['sida']}"
        )
    rader.append("")

    for avs in data["avsnitt"]:
        rader.append(f"## {avs['titel']}")
        rader.append("")
        if avs["del"] == "B":
            rader.append(
                "Besvara frågorna med din tolkning av regelverket och ange vilken "
                "punkt du hänvisar till. SS 436 40 00 är uppbyggd av 7 delar "
                "(t.ex. del 5), som innehåller kapitel (51), avsnitt (512) och "
                "punkter (512.2, 512.2.2)."
            )
            rader.append("")
        for fraga in avs["fragor"]:
            skriv_fraga(rader, fraga)

    MD_UT.write_text("\n".join(rader).rstrip() + "\n", encoding="utf-8")
    print(f"Skrev {MD_UT.name}: {data['antal_fragor']} frågor")


if __name__ == "__main__":
    main()
