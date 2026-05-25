"""Pydantic models for ModelMirror schemas."""

from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional, Union

from pydantic import BaseModel, ConfigDict, Field


class Conversation(BaseModel):
    system: str
    developer: str = ""
    user: str


class RetrievedSnippet(BaseModel):
    id: str
    source: str
    text: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ContextBlock(BaseModel):
    retrieved_snippets: List[RetrievedSnippet] = Field(default_factory=list)


class ToolDefinition(BaseModel):
    name: str
    description: str = ""
    json_schema: Dict[str, Any] = Field(default_factory=dict)


class RuntimeBlock(BaseModel):
    mode: str
    constraints: Dict[str, Any]


class PackedPrompt(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1.0"]
    conversation: Conversation
    context: ContextBlock
    tools: List[ToolDefinition] = Field(default_factory=list)
    runtime: RuntimeBlock
    raw: Dict[str, Any]


class ToolCall(BaseModel):
    tool_name: str
    args: Dict[str, Any]


class FailureMode(BaseModel):
    code: str
    severity: Literal["HIGH", "MED", "LOW"]
    message: str
    evidence: Optional[Dict[str, Any]] = None


class SuggestionEntry(BaseModel):
    id: str
    applies_to: List[str]
    title: str
    lines: List[str]
    confidence: Literal["HIGH", "MED", "LOW"]
    rationale: str


class EvalDiagnostics(BaseModel):
    failure_modes: List[FailureMode] = Field(default_factory=list)
    suggestions: List[SuggestionEntry] = Field(default_factory=list)


class EvalNotes(BaseModel):
    missing_context: str = ""
    contradictions: str = ""
    assumptions: str = ""
    extra: Dict[str, Any] = Field(default_factory=dict)


class EvalResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1.0"]
    run_id: str
    bundle_sha256: str
    status: Literal["PASS", "FAIL"]
    chosen_action: Literal["RESPOND", "TOOL_CALL", "CLARIFY", "REFUSE"]
    drafted_text: str
    canonical_output: Union[str, Dict[str, Any]]
    tool_calls: List[ToolCall] = Field(default_factory=list)
    diagnostics: EvalDiagnostics = Field(default_factory=EvalDiagnostics)
    notes: EvalNotes = Field(default_factory=EvalNotes)


class RunManifest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    run_id: str
    timestamp_utc: str
    bundle_sha256: str
    schema_version: str
    operator_id: Optional[str] = None
