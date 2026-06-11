"""
Pipeline Stage Timer & Counter — CAS Extractor v0.2
Drop-in instrumentation. Zero dependencies beyond stdlib.

Usage:
    from pipeline_timer import StageTimer

    timer = StageTimer()
    with timer.stage("extraction"):
        # ... extraction code ...
        timer.count("symbols", 74)
        timer.count("imports", 59)

    timer.report()  # prints markdown table
"""

import time
import json
from contextlib import contextmanager
from collections import OrderedDict
from typing import Optional
from pathlib import Path


class StageTimer:
    def __init__(self):
        self._stages: OrderedDict[str, dict] = OrderedDict()
        self._current: Optional[str] = None
        self._wall_start = time.monotonic()

    @contextmanager
    def stage(self, name: str):
        """Context manager for timing a pipeline stage."""
        self._current = name
        self._stages[name] = {
            "start": time.monotonic(),
            "end": None,
            "elapsed_s": None,
            "counters": {},
            "notes": [],
        }
        try:
            yield
        except Exception as e:
            self._stages[name]["notes"].append(f"FAILED: {type(e).__name__}: {e}")
            raise
        finally:
            end = time.monotonic()
            self._stages[name]["end"] = end
            self._stages[name]["elapsed_s"] = round(end - self._stages[name]["start"], 3)
            self._current = None

    def count(self, key: str, value: int = 1, stage: Optional[str] = None):
        """Increment a counter for the current (or named) stage."""
        target = stage or self._current
        if target and target in self._stages:
            c = self._stages[target]["counters"]
            c[key] = c.get(key, 0) + value

    def note(self, msg: str, stage: Optional[str] = None):
        """Attach a note to the current (or named) stage."""
        target = stage or self._current
        if target and target in self._stages:
            self._stages[target]["notes"].append(msg)

    def report(self, file: Optional[Path] = None) -> str:
        """Generate a markdown report. Optionally write to file."""
        wall_total = round(time.monotonic() - self._wall_start, 3)
        lines = []
        lines.append("## Pipeline Stage Timings\n")
        lines.append(f"| Stage | Time (s) | % of Total | Counters |")
        lines.append(f"|-------|----------|------------|----------|")

        for name, data in self._stages.items():
            elapsed = data["elapsed_s"] or 0
            pct = round(elapsed / wall_total * 100, 1) if wall_total > 0 else 0
            counters_str = ", ".join(
                f"{k}={v}" for k, v in data["counters"].items()
            ) or "—"
            status = "❌ " if any("FAILED" in n for n in data["notes"]) else ""
            lines.append(f"| {status}{name} | {elapsed:.3f} | {pct}% | {counters_str} |")

        lines.append(f"\n**Wall total: {wall_total:.3f}s**\n")

        # Notes section
        has_notes = any(data["notes"] for data in self._stages.values())
        if has_notes:
            lines.append("### Notes\n")
            for name, data in self._stages.items():
                for note in data["notes"]:
                    lines.append(f"- **{name}**: {note}")

        report_text = "\n".join(lines)

        if file:
            file.write_text(report_text, encoding="utf-8")

        return report_text

    def to_json(self) -> str:
        """Export raw timing data as JSON (for programmatic use)."""
        return json.dumps(
            {name: {
                "elapsed_s": d["elapsed_s"],
                "counters": d["counters"],
                "notes": d["notes"],
            } for name, d in self._stages.items()},
            indent=2
        )
