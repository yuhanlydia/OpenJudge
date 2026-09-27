from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Protocol
RawNote = dict[str, Any]
class OpenReviewClient(Protocol):
    def get_group(self, id: str) -> RawNote: ...
    def get_invitation(self, id: str) -> RawNote: ...
    def get_notes(self, **params: Any) -> RawNote: ...
@dataclass
class DiscoveryResult:
    discovered_config: dict[str,Any]
    raw_schema_hash: str
    sample_ids: list[str] = field(default_factory=list)
    validation_errors: list[str] = field(default_factory=list)
@dataclass
class RawCapture:
    capture_id: str
    directory: str
    venue_schema_hash: str
    pages: list[dict[str,Any]]
    success_count: int
    failure_count: int
    capture_complete: bool
@dataclass
class NormalizedCorpus:
    papers: list[dict[str,Any]]
    reviews: list[dict[str,Any]]
    coverage: dict[str,Any]
    issues: list[dict[str,Any]]
    snapshot_id: str
@dataclass
class EvidenceBundle:
    bundle_id: str
    forum_id: str
    versioned_sources: list[dict[str,Any]]
    coverage: dict[str,Any]
    bundle_hash: str
@dataclass
class ValidationResult:
    ok: bool
    errors: list[dict[str,Any]]
    warnings: list[dict[str,Any]] = field(default_factory=list)
