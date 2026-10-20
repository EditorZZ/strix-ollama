"""Check Strix's Ollama connection and streamed tool calls without starting a scan."""

# ruff: noqa: INP001 -- standalone command-line script

import argparse
import asyncio
from pathlib import Path

import httpx
from agents import Agent, RunConfig, Runner, function_tool
from rich.console import Console

from strix.config import apply_config_override, load_settings
from strix.config.models import StrixProvider
from strix.core.inputs import make_model_settings
from strix.interface.scan_setup import preflight_model_connection
from strix.llm.context_budget import context_window


async def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, help="Strix JSON configuration to check")
    args = parser.parse_args()
    if args.config:
        path = args.config.expanduser().resolve()
        if not path.is_file():
            parser.error(f"Config file not found: {path}")
        apply_config_override(path)
    settings = load_settings()
    model = settings.llm.model or ""
    if not model.startswith(("ollama/", "ollama_chat/")):
        raise SystemExit("Configure an Ollama model before running this check.")

    console = Console()
    console.print(f"Model: {model}")
    console.print(f"Endpoint: {settings.llm.api_base}")
    budget = context_window(model)
    async with httpx.AsyncClient(timeout=15) as client:
        base = (settings.llm.api_base or "http://127.0.0.1:11434").rstrip("/")
        tags = await client.get(f"{base}/api/tags")
        tags.raise_for_status()
        name = model.split("/", 1)[1]
        entry = next(
            (item for item in tags.json()["models"] if item["name"] == name),
            {},
        )
        if entry.get("remote_model"):
            shown = await client.post(f"{base}/api/show", json={"model": name})
            shown.raise_for_status()
            info = shown.json().get("model_info", {})
            limits = [value for key, value in info.items() if key.endswith(".context_length")]
            if not limits or budget > min(limits):
                raise SystemExit("Strix context budget exceeds or cannot verify cloud capacity.")
            console.print(f"Ollama Cloud model: {entry['remote_model']}")
        else:
            configured_context = (settings.llm.extra_body or {}).get("options", {}).get("num_ctx")
            if configured_context is None or budget > configured_context:
                raise SystemExit("Set Ollama options.num_ctx to at least the Strix context budget.")
    console.print(f"Strix context budget: {budget} tokens")
    await preflight_model_connection(model, settings=settings)
    console.print("Model connection: OK")

    received: list[str] = []

    @function_tool
    def connection_check(value: str) -> str:
        """Echo the connection test value. This tool has no external effects."""
        received.append(value)
        return value

    agent = Agent(
        name="Ollama connection check",
        instructions=(
            "Call connection_check exactly once with value='strix-ollama-ok'. "
            "After receiving its result, reply with exactly OK. Do nothing else."
        ),
        model=model,
        model_settings=make_model_settings(
            settings.llm.reasoning_effort,
            model_name=model,
            request_timeout=settings.llm.timeout,
            prompt_cache=False,
            extra_body=settings.llm.extra_body,
        ),
        tools=[connection_check],
    )
    result = Runner.run_streamed(
        agent,
        "Perform the connection check now.",
        max_turns=3,
        run_config=RunConfig(model_provider=StrixProvider(), tracing_disabled=True),
    )
    async with asyncio.timeout(settings.llm.timeout):
        async for _event in result.stream_events():
            pass
    if received != ["strix-ollama-ok"] or str(result.final_output).strip() != "OK":
        raise RuntimeError(
            f"Unexpected tool round trip: {received!r}; final output: {result.final_output!r}"
        )
    console.print("Streamed tool call and tool result round trip: OK")


if __name__ == "__main__":
    asyncio.run(main())
