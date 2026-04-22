from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ArtifactBundle:
    user_request: str
    files: dict[str, str]
    prompts: dict[str, str]


@dataclass
class AgentResult:
    agent_name: str
    summary: str
    details: list[str] = field(default_factory=list)


@dataclass
class Finding:
    finding_id: str
    title: str
    severity: str
    confidence: str
    impact: str
    evidence: list[str]
    remediation: list[str]


@dataclass
class ReviewState:
    goal: str
    artifacts: ArtifactBundle
    agent_results: list[AgentResult] = field(default_factory=list)
    stable_facts: list[str] = field(default_factory=list)
    candidate_findings: list[str] = field(default_factory=list)
    accepted_findings: list[Finding] = field(default_factory=list)
    evidence_gaps: list[str] = field(default_factory=list)
    final_report: str = ""

    def render_console(self) -> str:
        lines = [
            "# IDOR Agent Team Demo",
            "",
            "## User Request",
            self.goal,
            "",
            "## Agent Trace",
        ]
        for result in self.agent_results:
            lines.append(f"### {result.agent_name}")
            lines.append(f"- Summary: {result.summary}")
            for detail in result.details:
                lines.append(f"- {detail}")
            lines.append("")

        lines.extend(
            [
                "## Final Report",
                self.final_report,
            ]
        )
        return "\n".join(lines)
