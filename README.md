# Strix für Ollama

Strix mit **Ollama Cloud oder lokalen Ollama-Modellen** für automatisierte
Sicherheitstests. Dieses Repository enthält fertige ENV-Vorlagen, JSON-Profile
und einen Verbindungstest für beide Betriebsarten.

Strix läuft auf deinem Rechner und nutzt Docker für seine Testumgebung.
Die Modellanbindung erfolgt über deinen laufenden Ollama-Dienst.

## Voraussetzungen

- [Ollama](https://ollama.com/download), installiert und gestartet
- Docker, installiert und gestartet
- Python 3.12 oder neuer
- [uv](https://docs.astral.sh/uv/) für die Python-Installation
- Go 1.24 oder neuer für die interaktive Oberfläche; die Go-Toolchain kann
  entsprechend der im Repository festgelegten Version automatisch aktualisiert werden
- Für Ollama Cloud: ein bei Ollama angemeldetes Konto mit verfügbarer Cloud-Nutzung

## Installation

```sh
git clone https://github.com/EditorZZ/strix-ollama.git
cd strix-ollama
uv sync --frozen --no-dev
```

## 1. Ollama Cloud starten

Das vorbereitete Cloud-Profil verwendet **Gemma 4**. Ollama übernimmt die
Anmeldung und leitet die Modellanfragen an Ollama Cloud weiter. In Strix ist
dafür kein zusätzlicher API-Schlüssel nötig.

```sh
ollama signin
ollama pull gemma4:31b-cloud

cp .env.ollama-cloud.example .env
set -a
source .env
set +a

.venv/bin/strix
```

Die Oberfläche öffnet sich; dort kannst du das autorisierte Testziel angeben.
Cloud-Anfragen werden über dein Ollama-Konto verarbeitet und unterliegen dessen
Nutzungslimits. Prompts und Werkzeugergebnisse im Modellkontext gehen dabei an
Ollama Cloud.

Die wesentlichen ENV-Einstellungen der Vorlage sind:

```sh
STRIX_LLM=ollama/gemma4:31b-cloud
LLM_API_BASE=http://127.0.0.1:11434
LLM_EXTRA_BODY='{"think":false}'
```

Die vollständige Vorlage enthält zusätzlich passende Kontext- und Zeitlimits.
**Strix lädt `.env` nicht automatisch:** Die oben gezeigten `source`- und
`set -a`-Befehle exportieren die Einstellungen in der aktuellen Shell.
Die persönliche `.env`-Datei wird nicht in Git aufgenommen.

## 2. Ollama lokal starten

Für die lokale Modellberechnung verwendet das zweite Profil **Qwen3 8B**.
Ein Ollama-Cloud-Konto ist dafür nicht erforderlich.

```sh
ollama pull huihui_ai/qwen3-abliterated:latest

cp .env.ollama-local.example .env
set -a
source .env
set +a

.venv/bin/strix
```

Beim Wechsel zwischen den beiden ENV-Vorlagen werden die Einstellungen für das
jeweilige Profil neu geladen. Sichere eine selbst angepasste `.env`, bevor du sie
mit einer Vorlage überschreibst.

| Einstellung | Ollama Cloud | Ollama lokal |
| --- | --- | --- |
| Modell | `gemma4:31b-cloud` | `huihui_ai/qwen3-abliterated:latest` |
| Ollama-Endpunkt | `http://127.0.0.1:11434` | `http://127.0.0.1:11434` |
| Modellberechnung | Ollama Cloud | Eigener Rechner |
| Kontext | 262.144 Tokens | 40.960 Tokens |
| Thinking | Deaktiviert | Deaktiviert |
| Bildkontext | Aktiviert | Deaktiviert |
| Strix-Telemetrie | Deaktiviert | Deaktiviert |

Die Modellqualität beeinflusst die Ergebnisse. Der Verbindungstest prüft die
technische Anbindung; er bewertet nicht die Qualität vollständiger Pentests.
Das lokale 8B-Modell kann bei komplexen Agentenaufgaben unzuverlässig sein.

## Verbindung prüfen

Nach dem Laden der gewünschten ENV-Vorlage:

```sh
.venv/bin/python scripts/check_ollama.py
```

Der Test prüft die Kontextgröße, eine Modellantwort sowie einen gestreamten
Werkzeugaufruf mit Rückgabe. Er startet keinen Pentest. Beide vorbereiteten
Profile wurden am 20.10.2026 erfolgreich mit diesem Test geprüft.

## Alternativ: JSON statt ENV

In einer Shell ohne vorherige Strix-ENV-Exporte kannst du die Konfiguration direkt
beim Start auswählen:

```sh
# Ollama Cloud
.venv/bin/strix --config ollama-cloud-config.json

# Ollama lokal
.venv/bin/strix --config ollama-config.json
```

Umgebungsvariablen haben Vorrang vor JSON-Dateien. Die Profile lassen sich auch
mit `scripts/check_ollama.py --config <Datei>` prüfen.

## Einen Test starten

Nach dem Laden deiner Ollama-Konfiguration kannst du ein autorisiertes Ziel
direkt übergeben:

```sh
.venv/bin/strix --target /absoluter/pfad/zum/projekt --scan-mode quick
```

Beim ersten Scan lädt Strix bei Bedarf seine Docker-Sandbox.
Ergebnisse liegen unter `strix_runs/<run-name>/`.
Lokale Zielverzeichnisse werden für die Sandbox schreibbar eingebunden.

## Modell und Einstellungen ändern

In deiner `.env` kannst du `STRIX_LLM` auf `ollama/<Modellname>` ändern.
Verfügbare lokale und eingerichtete Cloud-Modelle zeigt `ollama list`.
Bei einem anderen Ollama-Server passt du `LLM_API_BASE` an.
Das Modell muss strukturierte Werkzeugaufrufe unterstützen; Kontextgröße und
Thinking-Einstellung müssen zum gewählten Modell passen.

Weitere Details: [Ollama-Startanleitung](OLLAMA-START.md) und
[offizielle Ollama-Cloud-Dokumentation](https://docs.ollama.com/cloud).

## Herkunft und Lizenz

Dieses Repository basiert auf [usestrix/strix](https://github.com/usestrix/strix),
Version 1.7.0, Ausgangscommit `a0f8ea2cd379c4bf56e665d3db2ba8a4f7c0683c`.
Strix unterstützt Ollama bereits nativ. Diese Erweiterung ergänzt die
Ollama-Konfigurationsvorlagen, den Verbindungstest und die Anleitung.

Die ursprüngliche Git-Historie bleibt erhalten. Lizenz: [Apache-2.0](LICENSE).
