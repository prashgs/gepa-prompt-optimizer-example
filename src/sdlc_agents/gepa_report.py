"""Capture GEPA optimization events and write Markdown reports."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import json


def _fence(text: str, lang: str = "") -> str:
    body = (text or "").rstrip()
    return f"```{lang}\n{body}\n```"


def _md_escape_heading(text: str) -> str:
    return text.replace("\n", " ").strip()


@dataclass
class ReflectionRecord:
    iteration: int
    parent_prompt: str
    reflective_dataset: dict[str, list[dict[str, Any]]]
    reflection_prompts: dict[str, str | list[dict[str, Any]]]
    raw_lm_outputs: dict[str, str]
    proposed_instructions: dict[str, str]
    accepted: bool | None = None
    reason: str | None = None
    old_score: float | None = None
    new_score: float | None = None


@dataclass
class RoleOptimizationTrace:
    role: str
    task_lm: str
    reflection_lm: str
    max_metric_calls: int
    seed_prompt: str
    trainset: list[dict[str, Any]]
    reflections: list[ReflectionRecord] = field(default_factory=list)
    candidates: list[dict[str, str]] = field(default_factory=list)
    val_scores: list[float] = field(default_factory=list)
    best_idx: int = 0
    selected_prompt: str = ""
    selected_reason: str = ""
    total_metric_calls: int | None = None

    def record_proposal_end(self, event: dict[str, Any]) -> None:
        parent = event.get("parent_candidate") or {}
        self.reflections.append(
            ReflectionRecord(
                iteration=int(event.get("iteration", len(self.reflections) + 1)),
                parent_prompt=str(parent.get("system_prompt", "")),
                reflective_dataset=dict(event.get("reflective_dataset") or {}),
                reflection_prompts=dict(event.get("prompts") or {}),
                raw_lm_outputs=dict(event.get("raw_lm_outputs") or {}),
                proposed_instructions=dict(event.get("new_instructions") or {}),
            )
        )

    def mark_accepted(self, event: dict[str, Any]) -> None:
        if not self.reflections:
            return
        rec = self.reflections[-1]
        rec.accepted = True
        rec.new_score = float(event.get("new_score")) if event.get("new_score") is not None else None

    def mark_rejected(self, event: dict[str, Any]) -> None:
        if not self.reflections:
            return
        rec = self.reflections[-1]
        rec.accepted = False
        rec.reason = str(event.get("reason") or "rejected")
        if event.get("old_score") is not None:
            rec.old_score = float(event["old_score"])
        if event.get("new_score") is not None:
            rec.new_score = float(event["new_score"])


class OptimizationReportCallback:
    """GEPA callback that records inputs and reflection proposals for Markdown reports."""

    def __init__(self, trace: RoleOptimizationTrace) -> None:
        self.trace = trace
        self._pending_reflective: dict[str, list[dict[str, Any]]] = {}
        self._pending_parent: str = ""

    def on_proposal_start(self, event: dict[str, Any]) -> None:
        self._pending_reflective = dict(event.get("reflective_dataset") or {})
        parent = event.get("parent_candidate") or {}
        self._pending_parent = str(parent.get("system_prompt", ""))

    def on_proposal_end(self, event: dict[str, Any]) -> None:
        # Ensure reflective dataset / parent are present even if only on start event
        merged = dict(event)
        if not merged.get("reflective_dataset") and self._pending_reflective:
            merged["reflective_dataset"] = self._pending_reflective
        parent = merged.get("parent_candidate") or {}
        if not parent.get("system_prompt") and self._pending_parent:
            merged["parent_candidate"] = {
                **parent,
                "system_prompt": self._pending_parent,
            }
        self.trace.record_proposal_end(merged)
        self._pending_reflective = {}
        self._pending_parent = ""

    def on_candidate_accepted(self, event: dict[str, Any]) -> None:
        self.trace.mark_accepted(event)

    def on_candidate_rejected(self, event: dict[str, Any]) -> None:
        self.trace.mark_rejected(event)


def render_role_markdown(trace: RoleOptimizationTrace) -> str:
    """Render a single-role optimization report."""
    lines: list[str] = []
    lines.append(f"# GEPA Optimization Report — `{trace.role}`")
    lines.append("")
    lines.append(f"_Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}_")
    lines.append("")
    lines.append("## Configuration")
    lines.append("")
    lines.append(f"- **Role:** `{trace.role}`")
    lines.append(f"- **Task LM:** `{trace.task_lm}`")
    lines.append(f"- **Reflection LM:** `{trace.reflection_lm}`")
    lines.append(f"- **Max metric calls:** `{trace.max_metric_calls}`")
    if trace.total_metric_calls is not None:
        lines.append(f"- **Total metric calls used:** `{trace.total_metric_calls}`")
    lines.append("")

    lines.append("## Input")
    lines.append("")
    lines.append("### Seed system prompt")
    lines.append("")
    lines.append(_fence(trace.seed_prompt))
    lines.append("")
    lines.append("### Training examples")
    lines.append("")
    for i, ex in enumerate(trace.trainset, start=1):
        lines.append(f"#### Example {i}")
        lines.append("")
        lines.append(f"- **Input:** {_md_escape_heading(str(ex.get('input', '')))}")
        answer = ex.get("answer", "")
        lines.append(f"- **Expected answer keyword:** `{answer}`")
        ctx = ex.get("additional_context") or {}
        if ctx:
            lines.append(f"- **Additional context:** `{ctx}`")
        lines.append("")

    lines.append("## Reflections")
    lines.append("")
    if not trace.reflections:
        lines.append("_No reflection proposals were produced in this run "
                     "(budget may have been spent on evaluation only)._")
        lines.append("")
    else:
        for rec in trace.reflections:
            status = (
                "accepted"
                if rec.accepted is True
                else "rejected"
                if rec.accepted is False
                else "unknown"
            )
            lines.append(f"### Iteration {rec.iteration} — proposal **{status}**")
            lines.append("")
            if rec.old_score is not None or rec.new_score is not None:
                lines.append(
                    f"- Scores: old=`{rec.old_score}` → new=`{rec.new_score}`"
                    + (f" ({rec.reason})" if rec.reason else "")
                )
                lines.append("")

            lines.append("#### Parent prompt (before reflection)")
            lines.append("")
            lines.append(_fence(rec.parent_prompt))
            lines.append("")

            if rec.reflective_dataset:
                lines.append("#### Reflective dataset (feedback side-info)")
                lines.append("")
                lines.append(
                    _fence(
                        json.dumps(rec.reflective_dataset, indent=2, default=str),
                        "json",
                    )
                )
                lines.append("")

            if rec.reflection_prompts:
                lines.append("#### Prompt sent to reflection LM")
                lines.append("")
                for component, prompt in rec.reflection_prompts.items():
                    lines.append(f"**Component `{component}`**")
                    lines.append("")
                    if isinstance(prompt, list):
                        lines.append(_fence(str(prompt), "json"))
                    else:
                        lines.append(_fence(str(prompt)))
                    lines.append("")

            if rec.raw_lm_outputs:
                lines.append("#### Reflection LM raw output")
                lines.append("")
                for component, raw in rec.raw_lm_outputs.items():
                    lines.append(f"**Component `{component}`**")
                    lines.append("")
                    lines.append(_fence(str(raw)))
                    lines.append("")

            if rec.proposed_instructions:
                lines.append("#### Proposed new prompt")
                lines.append("")
                for component, text in rec.proposed_instructions.items():
                    lines.append(f"**Component `{component}`**")
                    lines.append("")
                    lines.append(_fence(str(text)))
                    lines.append("")

    lines.append("## Candidate scores")
    lines.append("")
    if not trace.val_scores:
        lines.append("_No validation scores recorded._")
        lines.append("")
    else:
        lines.append("| Candidate idx | Val score | Notes |")
        lines.append("|--------------:|----------:|-------|")
        for idx, score in enumerate(trace.val_scores):
            notes: list[str] = []
            if idx == 0:
                notes.append("seed")
            if idx == trace.best_idx:
                notes.append("GEPA best")
            lines.append(f"| {idx} | {score:.3f} | {', '.join(notes)} |")
        lines.append("")

    lines.append("## Final selected prompt")
    lines.append("")
    lines.append(f"**Reason:** {trace.selected_reason}")
    lines.append("")
    lines.append(_fence(trace.selected_prompt))
    lines.append("")
    return "\n".join(lines)


def write_role_report(trace: RoleOptimizationTrace, report_dir: Path) -> Path:
    report_dir.mkdir(parents=True, exist_ok=True)
    path = report_dir / f"{trace.role}.md"
    path.write_text(render_role_markdown(trace), encoding="utf-8")
    return path


def write_combined_report(traces: list[RoleOptimizationTrace], report_dir: Path) -> Path:
    report_dir.mkdir(parents=True, exist_ok=True)
    path = report_dir / "optimization_report.md"
    lines: list[str] = []
    lines.append("# GEPA Optimization Report")
    lines.append("")
    lines.append(f"_Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}_")
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    lines.append("| Role | Reflections | GEPA best score | Selected reason |")
    lines.append("|------|-------------|-----------------|-----------------|")
    for t in traces:
        best = t.val_scores[t.best_idx] if t.val_scores else float("nan")
        reason = t.selected_reason.replace("|", "/")
        lines.append(
            f"| [`{t.role}`](./{t.role}.md) | {len(t.reflections)} | {best:.3f} | {reason} |"
        )
    lines.append("")
    for t in traces:
        lines.append("---")
        lines.append("")
        lines.append(render_role_markdown(t))
    path.write_text("\n".join(lines), encoding="utf-8")
    return path
