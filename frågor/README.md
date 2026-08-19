# frågor/

Övningsuppgifterna till kursen Elinstallation, uttagna ur käll-PDF:en och
indexerade så att de går att söka i, länka till och plugga på.

| Fil | Roll |
|---|---|
| `INDEX.md` | Läsbart index — alla 279 frågor per kapitel. **Genererad, redigera inte.** |
| `fragor.json` | Källan. Rätta frågetext här. |
| `bilder/` | Figurer utplockade ur PDF:en. |
| `Övningsuppgifter Montörshandbok och Faktabok.pdf` | Originalet, som sidhänvisningarna pekar på. |
| `verktyg/` | Skripten som bygger de två första. |

## Ändra något

Rätta i `fragor.json` och generera om:

```bash
python3 verktyg/generera_index.py
```

`verktyg/extrahera.py` läser om hela PDF:en och skriver över både `fragor.json`
och `bilder/`. Kör det **bara** när käll-PDF:en byts ut — annars går
handrättningar i JSON-filen förlorade. Det kräver `pypdf` och `pillow`:

```bash
pip install pypdf pillow
```

## Om numreringen

Frågorna behåller numren från PDF:en, så att "fråga 142" betyder samma sak här
som i original.

- **1–219** — del A, grupperad per Faktabok-kapitel (flera parade med ett
  Montörshandbok-kapitel).
- **73.1–73.7** — delfrågor till offert-caset i fråga 73, som i PDF:en har en
  egen numrering 1–7.
- **B1–B53** — del B om Elinstallationsreglerna SS 436 40 00. Serien börjar om
  på 1 i PDF:en och har prefixats för att inte krocka med del A.

## Om bilderna

13 frågor går inte att besvara utan sin figur. Vilka de är går inte att avgöra
maskinellt — "nedanstående" syftar oftast på en punktlista, medan fråga 199
("den här dosdimmern") behöver sin bild utan att nämna ordet bild. Kopplingen är
därför en genomgången tabell i `verktyg/extrahera.py`, inte en gissning.

Två foton är rena illustrationer, och fråga B48 hänvisar till en "bilaga A" som
inte följer med PDF:en.
