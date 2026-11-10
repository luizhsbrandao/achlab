"""Modelo de dados do achlab.

O projeto é um JSON versionado. O modelo não conhece scoring nem CLI: só estrutura e
validação de integridade.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

SCHEMA_VERSION = 1
CONSISTENCIES = {"++", "+", "0", "-", "--", "na"}
RELIABILITIES = {"A", "B", "C", "D", "E", "F"}
CREDIBILITIES = {1, 2, 3, 4, 5, 6}
RELEVANCES = {"alta", "media", "baixa"}
STATUSES = {"ativa", "rejeitada"}
EVIDENCE_STATUSES = {"draft", "aceita", "rejeitada"}


@dataclass
class Source:
    citation: str = ""
    url: str = ""
    archive_url: str = ""
    locator: str = ""
    accessed_at: str = ""

    def has_locator(self) -> bool:
        return any(s.strip() for s in (self.url, self.archive_url, self.locator))

    def to_dict(self) -> dict[str, str]:
        return {
            "citation": self.citation,
            "url": self.url,
            "archive_url": self.archive_url,
            "locator": self.locator,
            "accessed_at": self.accessed_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> Source:
        data = data or {}
        return cls(
            citation=str(data.get("citation", "")),
            url=str(data.get("url", "")),
            archive_url=str(data.get("archive_url", "")),
            locator=str(data.get("locator", "")),
            accessed_at=str(data.get("accessed_at", "")),
        )


@dataclass
class Assessment:
    consistency: str
    rationale: str
    author: str = ""
    ts: str = ""

    def to_dict(self) -> dict[str, str]:
        return {
            "consistency": self.consistency,
            "rationale": self.rationale,
            "author": self.author,
            "ts": self.ts,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Assessment:
        return cls(
            consistency=str(data.get("consistency", "na")),
            rationale=str(data.get("rationale", "")),
            author=str(data.get("author", "")),
            ts=str(data.get("ts", "")),
        )


@dataclass
class Hypothesis:
    id: str
    statement: str
    definition: str = ""
    indicators: list[str] = field(default_factory=list)
    status: str = "ativa"
    rejection_reason: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "statement": self.statement,
            "definition": self.definition,
            "indicators": list(self.indicators),
            "status": self.status,
            "rejection_reason": self.rejection_reason,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Hypothesis:
        return cls(
            id=str(data.get("id", "")),
            statement=str(data.get("statement", "")),
            definition=str(data.get("definition", "")),
            indicators=[str(i) for i in data.get("indicators", [])],
            status=str(data.get("status", "ativa")),
            rejection_reason=str(data.get("rejection_reason", "")),
        )


@dataclass
class Evidence:
    id: str
    title: str
    source: Source
    reliability: str
    credibility: int
    relevance: str
    excerpt: str
    status: str = "draft"
    date_of_information: str = ""
    assessments: dict[str, Assessment] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "source": self.source.to_dict(),
            "reliability": self.reliability,
            "credibility": self.credibility,
            "relevance": self.relevance,
            "excerpt": self.excerpt,
            "status": self.status,
            "date_of_information": self.date_of_information,
            "assessments": {k: v.to_dict() for k, v in sorted(self.assessments.items())},
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Evidence:
        return cls(
            id=str(data.get("id", "")),
            title=str(data.get("title", "")),
            source=Source.from_dict(data.get("source")),
            reliability=str(data.get("reliability", "")),
            credibility=int(data.get("credibility", 0)),
            relevance=str(data.get("relevance", "")),
            excerpt=str(data.get("excerpt", "")),
            status=str(data.get("status", "draft")),
            date_of_information=str(data.get("date_of_information", "")),
            assessments={
                str(k): Assessment.from_dict(v)
                for k, v in (data.get("assessments") or {}).items()
            },
        )

    def consistency(self, hypothesis_id: str) -> str:
        assessment = self.assessments.get(hypothesis_id)
        return assessment.consistency if assessment else "na"


@dataclass
class Project:
    question: str
    hypotheses: list[Hypothesis] = field(default_factory=list)
    evidence: list[Evidence] = field(default_factory=list)
    assumptions: list[dict[str, Any]] = field(default_factory=list)
    scope: str = ""
    analyst: str = ""
    created_at: str = ""
    classification: str = "UNCLASSIFIED"
    schema_version: int = SCHEMA_VERSION

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "question": self.question,
            "scope": self.scope,
            "analyst": self.analyst,
            "created_at": self.created_at,
            "classification": self.classification,
            "hypotheses": [h.to_dict() for h in self.hypotheses],
            "evidence": [e.to_dict() for e in self.evidence],
            "assumptions": list(self.assumptions),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Project:
        return cls(
            question=str(data.get("question", "")),
            hypotheses=[Hypothesis.from_dict(h) for h in data.get("hypotheses", [])],
            evidence=[Evidence.from_dict(e) for e in data.get("evidence", [])],
            assumptions=list(data.get("assumptions", [])),
            scope=str(data.get("scope", "")),
            analyst=str(data.get("analyst", "")),
            created_at=str(data.get("created_at", "")),
            classification=str(data.get("classification", "UNCLASSIFIED")),
            schema_version=int(data.get("schema_version", SCHEMA_VERSION)),
        )

    def active_hypotheses(self) -> list[Hypothesis]:
        return [h for h in self.hypotheses if h.status == "ativa"]

    def accepted_evidence(self) -> list[Evidence]:
        return [e for e in self.evidence if e.status == "aceita"]

    def hypothesis(self, hypothesis_id: str) -> Hypothesis | None:
        return next((h for h in self.hypotheses if h.id == hypothesis_id), None)

    def evidence_item(self, evidence_id: str) -> Evidence | None:
        return next((e for e in self.evidence if e.id == evidence_id), None)


def validate(project: Project) -> list[str]:
    """Erros de integridade. Lista vazia = projeto válido."""
    errors: list[str] = []
    if project.schema_version != SCHEMA_VERSION:
        errors.append(f"schema_version {project.schema_version} != {SCHEMA_VERSION}")
    if not project.question.strip():
        errors.append("pergunta vazia")

    hids = [h.id for h in project.hypotheses]
    eids = [e.id for e in project.evidence]
    if len(set(hids)) != len(hids):
        errors.append("ids de hipótese duplicados")
    if len(set(eids)) != len(eids):
        errors.append("ids de evidência duplicados")
    if not project.hypotheses:
        errors.append("projeto sem hipóteses")
    if not project.active_hypotheses():
        errors.append("projeto sem hipótese ativa")

    for h in project.hypotheses:
        if not h.id.strip() or not h.statement.strip():
            errors.append(f"{h.id or '?'}: id ou enunciado vazio")
        if h.status not in STATUSES:
            errors.append(f"{h.id}: status inválido ({h.status})")
        if h.status == "rejeitada" and not h.rejection_reason.strip():
            errors.append(f"{h.id}: hipótese rejeitada sem motivo")

    for e in project.evidence:
        if not e.id.strip() or not e.title.strip():
            errors.append(f"{e.id or '?'}: id ou título vazio")
        if e.reliability not in RELIABILITIES:
            errors.append(f"{e.id}: confiabilidade inválida ({e.reliability})")
        if e.credibility not in CREDIBILITIES:
            errors.append(f"{e.id}: credibilidade inválida ({e.credibility})")
        if e.relevance not in RELEVANCES:
            errors.append(f"{e.id}: relevância inválida ({e.relevance})")
        if e.status not in EVIDENCE_STATUSES:
            errors.append(f"{e.id}: status inválido ({e.status})")
        if e.status == "aceita":
            if not e.source.citation.strip():
                errors.append(f"{e.id}: evidência aceita sem citação")
            if not e.excerpt.strip():
                errors.append(f"{e.id}: evidência aceita sem trecho")
            if not e.source.has_locator():
                errors.append(f"{e.id}: evidência aceita sem localizador")
        for hid, a in e.assessments.items():
            if hid not in hids:
                errors.append(f"{e.id}: avaliação para hipótese inexistente ({hid})")
            if a.consistency not in CONSISTENCIES:
                errors.append(f"{e.id}/{hid}: consistência inválida ({a.consistency})")
            if not a.rationale.strip():
                errors.append(f"{e.id}/{hid}: avaliação sem justificativa")
    return errors
