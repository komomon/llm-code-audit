from __future__ import annotations

from pathlib import Path
import re

from idor_scaffold.loader import load_artifacts
from idor_scaffold.models import AgentResult, Finding, ReviewState


class ReviewOrchestrator:
    def __init__(self, root: Path) -> None:
        self.root = root

    def run(self) -> ReviewState:
        artifacts = load_artifacts(self.root)
        state = ReviewState(goal=artifacts.user_request, artifacts=artifacts)

        self._run_scope_agent(state)
        self._run_input_parameter_agent(state)
        self._run_auth_context_agent(state)
        self._run_call_chain_agent(state)
        self._run_input_auth_relation_agent(state)
        self._run_output_auth_relation_agent(state)
        self._run_idor_hypothesis_agent(state)
        self._run_evidence_agent(state)
        self._run_judge_agent(state)
        self._run_reporter_agent(state)

        return state

    def _run_scope_agent(self, state: ReviewState) -> None:
        routes = self._extract_routes(state.artifacts.files["routes.py"])
        details = [f"Identified review routes: {', '.join(routes)}"]
        details.append("Marked controller, service, repository, and serializer layers as hotspots.")
        state.stable_facts.extend(
            [
                "Routes exist for order detail read and order update.",
                "The review path spans controller, service, repository, and serializer layers.",
            ]
        )
        state.agent_results.append(
            AgentResult(
                agent_name="scope-agent",
                summary="Bounded the review to the order detail and order update paths.",
                details=details,
            )
        )

    def _run_input_parameter_agent(self, state: ReviewState) -> None:
        routes_text = state.artifacts.files["routes.py"]
        attacker_controlled = sorted(set(re.findall(r"<([a-zA-Z_][a-zA-Z0-9_]*)>", routes_text)))
        state.stable_facts.append(
            f"Attacker-controlled selectors identified from routes: {', '.join(attacker_controlled)}."
        )
        state.agent_results.append(
            AgentResult(
                agent_name="input-parameter-agent",
                summary="Found attacker-controlled resource selectors in the route layer.",
                details=[
                    f"Route parameters under attacker control: {', '.join(attacker_controlled)}",
                    "The same selector is reused for both read and update operations.",
                ],
            )
        )

    def _run_auth_context_agent(self, state: ReviewState) -> None:
        controller = state.artifacts.files["controllers/order.py"]
        auth_lines = []
        if "request.context.user" in controller:
            auth_lines.append("Trusted identity is read from request.context.user.")
            state.stable_facts.append("Trusted identity context is available in the controller.")
        if "if not user" in controller:
            auth_lines.append("Authentication is enforced before service invocation.")
            state.stable_facts.append("Visible code authenticates the caller before the service call.")
        auth_lines.append("No visible tenant field is read in the provided controller code.")
        state.agent_results.append(
            AgentResult(
                agent_name="auth-context-agent",
                summary="Mapped trusted authentication context in the controller layer.",
                details=auth_lines,
            )
        )

    def _run_call_chain_agent(self, state: ReviewState) -> None:
        details = [
            "Read path: routes.py -> controllers/order.py:get_order -> services/order_service.py:get_order -> repositories/order_repo.py:get_order -> serializers/order_serializer.py:to_json",
            "Write path: routes.py -> controllers/order.py:update_order -> services/order_service.py:update_order -> repositories/order_repo.py:get_order -> repositories/order_repo.py:save",
        ]
        state.stable_facts.extend(
            [
                "The read path fetches an order by id and serializes it for response.",
                "The write path fetches an order by id and updates it before save.",
            ]
        )
        state.agent_results.append(
            AgentResult(
                agent_name="call-chain-agent",
                summary="Traced both the read and update call chains from route to sink.",
                details=details,
            )
        )

    def _run_input_auth_relation_agent(self, state: ReviewState) -> None:
        repo = state.artifacts.files["repositories/order_repo.py"]
        details = []
        if 'find_one({"id": order_id})' in repo:
            details.append("Object selection uses order_id only in the repository.")
            state.stable_facts.append("Visible repository lookup is scoped by order_id only.")
        details.append("No visible comparison links order_id to current_user.id or tenant context.")
        details.append("No owner- or tenant-scoped predicate is visible in the repository layer.")
        state.agent_results.append(
            AgentResult(
                agent_name="input-auth-relation-agent",
                summary="Checked whether attacker-controlled selectors are constrained by trusted identity.",
                details=details,
            )
        )

    def _run_output_auth_relation_agent(self, state: ReviewState) -> None:
        service = state.artifacts.files["services/order_service.py"]
        serializer = state.artifacts.files["serializers/order_serializer.py"]
        details = []
        if "return order_serializer.to_json(order)" in service:
            details.append("The read path returns the fetched object to the caller.")
            state.stable_facts.append("The fetched object is returned after id-only lookup in the read path.")
        if "return order_repo.save(order)" in service:
            details.append("The update path mutates and saves the fetched object.")
            state.stable_facts.append("The fetched object is mutated after id-only lookup in the write path.")
        if "owner_id" in serializer:
            details.append("Serializer exposes owner_id but does not perform authorization checks.")
        details.append("No visible owner or tenant guard appears between object retrieval and response or mutation.")
        state.agent_results.append(
            AgentResult(
                agent_name="output-auth-relation-agent",
                summary="Checked whether returned or mutated objects are visibly scoped to trusted identity.",
                details=details,
            )
        )

    def _run_idor_hypothesis_agent(self, state: ReviewState) -> None:
        findings = [
            "Possible IDOR in the order detail flow because attacker-controlled order_id reaches id-only lookup and returned object has no visible owner scoping.",
            "Possible IDOR in the order update flow because attacker-controlled order_id reaches id-only lookup and mutated object has no visible owner scoping.",
        ]
        state.candidate_findings.extend(findings)
        state.agent_results.append(
            AgentResult(
                agent_name="idor-hypothesis-agent",
                summary="Generated candidate IDOR findings from stable facts and relation checks.",
                details=[
                    "Candidate read finding: object disclosure through route-controlled order_id.",
                    "Candidate write finding: object mutation through route-controlled order_id.",
                ],
            )
        )

    def _run_evidence_agent(self, state: ReviewState) -> None:
        state.agent_results.append(
            AgentResult(
                agent_name="evidence-agent",
                summary="Normalized the read and write IDOR paths into two distinct candidate findings.",
                details=[
                    "Kept read disclosure and write mutation separate because their impact differs.",
                    "Retained unresolved uncertainty about hidden policy or repository wrapper layers.",
                ],
            )
        )

    def _run_judge_agent(self, state: ReviewState) -> None:
        state.accepted_findings = [
            Finding(
                finding_id="IDOR-001",
                title="Order detail flow lacks visible object-level authorization",
                severity="high",
                confidence="medium",
                impact="An authenticated user may be able to read another user's order.",
                evidence=[
                    "routes.py",
                    "controllers/order.py",
                    "services/order_service.py",
                    "repositories/order_repo.py",
                    "serializers/order_serializer.py",
                ],
                remediation=[
                    "Scope object lookup by actor or tenant context.",
                    "Require a server-side ownership check before serializing the object.",
                ],
            ),
            Finding(
                finding_id="IDOR-002",
                title="Order update flow lacks visible object-level authorization",
                severity="high",
                confidence="medium",
                impact="An authenticated user may be able to update another user's order.",
                evidence=[
                    "routes.py",
                    "controllers/order.py",
                    "services/order_service.py",
                    "repositories/order_repo.py",
                ],
                remediation=[
                    "Scope object lookup by actor or tenant context before mutation.",
                    "Require a server-side ownership check before save.",
                ],
            ),
        ]
        state.evidence_gaps = [
            "No hidden decorator or policy implementation was provided.",
            "No repository wrapper or tenant helper was provided.",
        ]
        state.agent_results.append(
            AgentResult(
                agent_name="judge-agent",
                summary="Accepted one read-path IDOR finding and one write-path IDOR finding.",
                details=[
                    "Both findings are high severity because they expose unauthorized object access if true.",
                    "Confidence remains medium because hidden authorization layers could still exist outside the provided artifacts.",
                ],
            )
        )

    def _run_reporter_agent(self, state: ReviewState) -> None:
        lines = [
            "# IDOR Review: Order Detail and Update Flows",
            "",
            "## Scope",
            "",
            "Reviewed:",
            "",
            "- `sample_artifacts/routes.py`",
            "- `sample_artifacts/controllers/order.py`",
            "- `sample_artifacts/services/order_service.py`",
            "- `sample_artifacts/repositories/order_repo.py`",
            "- `sample_artifacts/serializers/order_serializer.py`",
            "",
            "## Executive Summary",
            "",
            "The visible code accepts attacker-controlled `order_id`, has trusted user context available, but does not show visible owner or tenant scoping during object retrieval. The fetched order is returned and updated after id-only lookup.",
            "",
            "## Findings",
            "",
        ]
        for finding in state.accepted_findings:
            lines.extend(
                [
                    f"### {finding.finding_id}: {finding.title}",
                    "",
                    f"- Severity: {finding.severity}",
                    f"- Confidence: {finding.confidence}",
                    f"- Impact: {finding.impact}",
                    "- Evidence:",
                ]
            )
            for item in finding.evidence:
                lines.append(f"  - `{item}`")
            lines.append("- Remediation:")
            for item in finding.remediation:
                lines.append(f"  - {item}")
            lines.append("")

        lines.extend(["## Unresolved Questions", ""])
        for gap in state.evidence_gaps:
            lines.append(f"- {gap}")

        state.final_report = "\n".join(lines)
        state.agent_results.append(
            AgentResult(
                agent_name="reporter-agent",
                summary="Rendered the final human-readable report from accepted findings.",
                details=["Preserved scope, evidence, impact, remediation, and unresolved gaps."],
            )
        )

    @staticmethod
    def _extract_routes(routes_text: str) -> list[str]:
        routes = re.findall(r'"([^"]+)"', routes_text)
        return list(dict.fromkeys(routes))
