import logging
from dataclasses import dataclass, field
from typing import Any
from uuid import uuid4

import httpx

from settings import get_settings

logger = logging.getLogger(__name__)


MAX_STRING_LENGTH = 1200
MAX_STEPS = 24


@dataclass
class TraceSendResult:
    trace_id: str | None
    status: str
    enabled: bool
    operations: list[str] = field(default_factory=list)
    steps: list[dict[str, Any]] = field(default_factory=list)
    error: str | None = None
    dashboard_url: str | None = None

    def metadata(self) -> dict[str, Any]:
        return {
            "enabled": self.enabled,
            "status": self.status,
            "trace_id": self.trace_id,
            "operations": self.operations,
            "steps": self.steps,
            "error": self.error,
            "dashboard_url": self.dashboard_url,
        }


def _clip(value: Any, limit: int = MAX_STRING_LENGTH) -> Any:
    if isinstance(value, str):
        compact = value.strip()
        return compact[: limit - 1].rstrip() + "…" if len(compact) > limit else compact
    if isinstance(value, list):
        return [_clip(item, limit) for item in value[:50]]
    if isinstance(value, dict):
        return {str(key)[:80]: _clip(item, limit) for key, item in value.items() if "key" not in str(key).lower() and "token" not in str(key).lower() and "secret" not in str(key).lower()}
    return value


def normalize_trace_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """Keep the dashboard contract small, serializable and safe for non-secret telemetry."""
    settings = get_settings()
    trace_id = str(payload.get("trace_id") or payload.get("session_id") or f"trace_{uuid4().hex[:16]}")
    operation = str(payload.get("operation") or "unknown_operation")
    steps = []
    for raw_step in payload.get("steps") or []:
        if not isinstance(raw_step, dict):
            continue
        step = {
            "step_type": str(raw_step.get("step_type") or "tool_call"),
            "name": str(raw_step.get("name") or "unnamed_step"),
        }
        if "input" in raw_step:
            step["input"] = _clip(raw_step["input"])
        if "output" in raw_step:
            step["output"] = _clip(raw_step["output"])
        if "metadata" in raw_step:
            step["metadata"] = _clip(raw_step["metadata"])
        steps.append(step)

    normalized = {
        "app_name": str(payload.get("app_name") or settings.observability_app_name),
        "trace_id": trace_id,
        "session_id": str(payload.get("session_id") or trace_id),
        "operation": operation,
        "model": str(payload.get("model") or "unknown"),
        "provider": str(payload.get("provider") or "unknown"),
        "status": str(payload.get("status") or "success"),
        "metadata": _clip(payload.get("metadata") or {}),
        "steps": steps[:MAX_STEPS],
    }
    for token_field in ("input_tokens", "output_tokens", "latency_ms", "cost_usd"):
        if token_field in payload:
            normalized[token_field] = payload[token_field]
    return normalized


async def send_analysis_trace(payload: dict[str, Any]) -> TraceSendResult:
    """Send an optional trace without ever breaking analysis/chat results."""
    settings = get_settings()
    normalized = normalize_trace_payload(payload)
    operations = [normalized["operation"]]
    for step in normalized["steps"]:
        name = step.get("name")
        if name and name not in operations:
            operations.append(str(name))

    if not settings.observability_enabled or not settings.observability_api_url:
        return TraceSendResult(
            trace_id=normalized["trace_id"],
            status="disabled",
            enabled=False,
            operations=operations,
            steps=normalized["steps"],
        )

    try:
        headers = {}
        if settings.observability_ingest_api_key:
            headers["Authorization"] = f"Bearer {settings.observability_ingest_api_key}"
        url = settings.observability_api_url.rstrip("/") + "/api/traces"
        async with httpx.AsyncClient(timeout=3.0) as client:
            response = await client.post(url, json=normalized, headers=headers)
            response.raise_for_status()
        response_trace_id = normalized["trace_id"]
        try:
            body = response.json()
            if isinstance(body, dict):
                response_trace_id = str(body.get("trace_id") or body.get("id") or response_trace_id)
        except ValueError:
            pass
        return TraceSendResult(
            trace_id=response_trace_id,
            status="sent",
            enabled=True,
            operations=operations,
            steps=normalized["steps"],
            dashboard_url=settings.observability_api_url.rstrip("/"),
        )
    except Exception as exc:  # pragma: no cover - defensive non-blocking integration
        logger.warning("observability trace failed: %s", exc)
        return TraceSendResult(
            trace_id=normalized["trace_id"],
            status="failed",
            enabled=True,
            operations=operations,
            steps=normalized["steps"],
            error=str(exc),
            dashboard_url=settings.observability_api_url.rstrip("/"),
        )
