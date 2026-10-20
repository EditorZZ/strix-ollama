# Strix mit Ollama und Ollama Cloud

Diese Erweiterung basiert auf [usestrix/strix](https://github.com/usestrix/strix)
(Apache-2.0). Sie ergänzt ENV-Beispiele, zwei fertige Konfigurationsprofile und
einen Verbindungstest. Strix unterstützt Ollama bereits nativ; der Provider-Code
bleibt unverändert.

Getestete Basis: Strix 1.7.0, Commit
`a0f8ea2cd379c4bf56e665d3db2ba8a4f7c0683c`, am 20.10.2026.

## Installation

Voraussetzungen: Python 3.12+, [uv](https://docs.astral.sh/uv/), Go für die
interaktive Oberfläche, laufendes Docker und [Ollama](https://ollama.com/download).
Im Repository-Verzeichnis:

```sh
uv sync --frozen --no-dev
```

## Ollama Cloud per ENV

Zuerst Ollama mit dem eigenen Konto anmelden und das Cloud-Modell verfügbar machen:

```sh
ollama signin
ollama pull gemma4:31b-cloud
```

Die fertige ENV-Vorlage kopieren und in der aktuellen Shell laden:

```sh
cp .env.ollama-cloud.example .env
set -a
source .env
set +a
.venv/bin/strix
```

Strix lädt `.env` nicht automatisch. `set -a` exportiert die geladenen Werte für
Strix. Die Datei `.env` ist vom Versionskontrollsystem ausgeschlossen.

Die wesentlichen Verbindungsvariablen sind:

```sh
export STRIX_LLM="ollama/gemma4:31b-cloud"
export LLM_API_BASE="http://127.0.0.1:11434"
export LLM_EXTRA_BODY='{"think":false}'
```

Die vollständige Vorlage setzt zusätzlich passende Kontext- und Zeitlimits.
Ollama übernimmt die Anmeldung und leitet Modellanfragen an Ollama Cloud weiter.
Im Repository ist kein API-Schlüssel enthalten. Prompts und Werkzeugergebnisse
im Modellkontext werden in der Cloud verarbeitet; es gelten die Nutzungslimits
des eigenen Kontos. Siehe [Ollama Cloud](https://docs.ollama.com/cloud).

## Lokales Ollama per ENV

Das lokale Profil verwendet ein Qwen3-Modell mit strukturierten Werkzeugaufrufen:

```sh
ollama pull huihui_ai/qwen3-abliterated:latest
cp .env.ollama-local.example .env
set -a
source .env
set +a
.venv/bin/strix
```

Das lokale Profil setzt 40.960 Kontext-Tokens, deaktiviert Thinking und
Bildkontext und verwendet Temperatur 0,2. Das Cloud-Profil verwendet
262.144 Kontext-Tokens und aktiviert Bildkontext. Beide deaktivieren die
Strix-Telemetrie.

Beim Modellwechsel `STRIX_LLM`, Kontextgröße und Thinking-Einstellung an das neue
Modell anpassen. Das Modell muss strukturierte Werkzeugaufrufe unterstützen.
Cloud-Modellnamen und Verfügbarkeit können sich ändern.

## Alternative: JSON-Profile

Ohne vorherige ENV-Exporte lassen sich die Profile direkt auswählen:

```sh
.venv/bin/strix --config ollama-cloud-config.json
.venv/bin/strix --config ollama-config.json
```

Umgebungsvariablen haben Vorrang vor JSON-Profilen. Zum Wechsel zwischen den
JSON-Profilen eine Shell ohne vorherige Strix-Exporte verwenden.
Die globale Standardkonfiguration liegt unter `~/.strix/cli-config.json`.

Für einen ausdrücklich autorisierten Test kann das Ziel direkt angegeben werden:

```sh
.venv/bin/strix --config ollama-cloud-config.json \
  --target /absoluter/pfad/zum/projekt --scan-mode quick
```

## Verbindung prüfen

```sh
.venv/bin/python scripts/check_ollama.py --config ollama-cloud-config.json
.venv/bin/python scripts/check_ollama.py --config ollama-config.json
```

Der Test prüft den Kontextabgleich, eine Modellantwort und einen gestreamten
Werkzeugaufruf samt Rückgabe. Das Testwerkzeug gibt lediglich einen festen
Testwert zurück. Es startet keinen Pentest und führt keine Modellbefehle auf dem
Rechner aus. Für das Cloud-Profil werden diese Testanfragen an die Cloud gesendet.

Beide Profile haben den Verbindungstest bestanden. Das belegt die technische
Anbindung; die Ergebnisqualität vollständiger Pentests wurde damit nicht geprüft.
Insbesondere das lokale 8B-Modell kann bei komplexen Agentenaufgaben unzuverlässig
sein.

## Sandbox und Wartung

Die verwendete Sandbox ist `ghcr.io/usestrix/strix-sandbox:1.3.0`.
Strix lädt sie beim ersten Scan, falls sie noch nicht vorhanden ist.

Abhängigkeiten des vorhandenen Repository-Stands wiederherstellen:

```sh
uv sync --frozen --no-dev
```
