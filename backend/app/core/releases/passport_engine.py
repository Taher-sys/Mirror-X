"""Release Passport generation engine.

Compiles verifiable multi-domain evidence across code changes, context drift findings,
synthetic scenario test runs, agent behavior telemetry, and policy evaluations.
Enforces truthful uncertainty disclosure without fabricating metrics.
"""

from typing import Any

from app.core.observability import trace_span
from app.models.release import ReleasePassport

VALID_PASSPORT_STATUSES = [
    "PASS",
    "FAIL",
    "WARNING",
    "HUMAN_REVIEW_REQUIRED",
    "NOT_EVALUATED",
]


class ReleasePassportEngine:
    """Evaluates readiness of a release bundle across all verification domains."""

    @staticmethod
    @trace_span("release.generate_passport")
    def generate_passport(
        release_version: str,
        changes: list[dict[str, Any]] | None = None,
        findings: list[dict[str, Any]] | None = None,
        scenarios: list[dict[str, Any]] | None = None,
        agent_runs: list[dict[str, Any]] | None = None,
        policy_decisions: list[dict[str, Any]] | None = None,
        evidence_records: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """Synthesize a complete verifiable Release Passport with cryptographic seal."""
        change_list = changes or []
        finding_list = findings or []
        scenario_list = scenarios or []
        agent_run_list = agent_runs or []
        decision_list = policy_decisions or []
        evidence_list = evidence_records or []

        uncertainty_disclosures: list[str] = []

        # 1. Code Change Analysis
        if not change_list:
            code_change_status = "NOT_EVALUATED"
            breaking_changes = 0
            max_risk = 0.0
            uncertainty_disclosures.append("No Git changes or PRs were linked to this release candidate.")
        else:
            breaking_changes = sum(len(c.get("impact_summary", {}).get("breaking_changes", [])) for c in change_list)
            max_risk = max((c.get("risk_score", 0.0) for c in change_list), default=0.0)
            if breaking_changes > 0:
                code_change_status = "HUMAN_REVIEW_REQUIRED"
                uncertainty_disclosures.append(
                    f"{breaking_changes} breaking schema/API changes require human sign-off."
                )
            elif max_risk >= 70.0:
                code_change_status = "WARNING"
            else:
                code_change_status = "PASS"

        code_change_analysis = {
            "status": code_change_status,
            "total_changes": len(change_list),
            "breaking_changes_count": breaking_changes,
            "max_risk_score": max_risk,
            "evidence_count": len(
                [e for e in evidence_list if e.get("evidence_type") in ["source_file", "graph_relationship"]]
            ),
        }

        # 2. Context Findings (Drift detection)
        critical_drifts = sum(1 for f in finding_list if f.get("severity") == "critical" and f.get("status") == "open")
        high_drifts = sum(1 for f in finding_list if f.get("severity") == "high" and f.get("status") == "open")
        open_drifts = sum(1 for f in finding_list if f.get("status") == "open")

        if not finding_list:
            context_status = "NOT_EVALUATED"
            uncertainty_disclosures.append("Context analysis scan has not been executed on reality graph.")
        elif critical_drifts > 0:
            context_status = "FAIL"
            uncertainty_disclosures.append(
                f"{critical_drifts} critical architecture/schema discrepancies remain unresolved."
            )
        elif high_drifts > 0:
            context_status = "WARNING"
            uncertainty_disclosures.append(f"{high_drifts} high-severity context findings detected.")
        else:
            context_status = "PASS"

        context_findings_summary = {
            "status": context_status,
            "total_findings": len(finding_list),
            "open_findings": open_drifts,
            "critical_count": critical_drifts,
            "high_count": high_drifts,
        }

        # 3. Scenario Testing
        if not scenario_list:
            scenario_status = "NOT_EVALUATED"
            passed_scenarios = 0
            failed_scenarios = 0
            uncertainty_disclosures.append("No synthetic test scenarios have been executed.")
        else:
            passed_scenarios = sum(
                1
                for s in scenario_list
                if s.get("status") == "passed" or (s.get("execution_result") or {}).get("passed")
            )
            failed_scenarios = sum(
                1
                for s in scenario_list
                if s.get("status") == "failed"
                or (s.get("execution_result") and not (s.get("execution_result") or {}).get("passed"))
            )
            if failed_scenarios > 0:
                scenario_status = "FAIL"
                uncertainty_disclosures.append(
                    f"{failed_scenarios} synthetic scenarios failed expected invariant checks."
                )
            elif passed_scenarios >= 3:
                scenario_status = "PASS"
            else:
                scenario_status = "WARNING"
                uncertainty_disclosures.append("Limited scenario coverage: fewer than 3 scenario classes evaluated.")

        scenario_testing_summary = {
            "status": scenario_status,
            "total_scenarios": len(scenario_list),
            "passed_count": passed_scenarios,
            "failed_count": failed_scenarios,
            "classes_tested": list(set(s.get("scenario_class", "unknown") for s in scenario_list)),
        }

        # 4. Agent Testing
        if not agent_run_list:
            agent_status = "NOT_EVALUATED"
            violations = 0
            uncertainty_disclosures.append("No agent runs or tool behaviors were captured in the Behavior Lab.")
        else:
            violations = sum((r.get("metrics") or r).get("policy_violations_count", 0) for r in agent_run_list)
            failures = sum(1 for r in agent_run_list if not (r.get("metrics") or r).get("successful_completion", False))
            if violations > 0:
                agent_status = "HUMAN_REVIEW_REQUIRED"
                uncertainty_disclosures.append(f"Agent execution incurred {violations} policy violation(s).")
            elif failures > 0:
                agent_status = "WARNING"
                uncertainty_disclosures.append(f"{failures} agent run(s) did not reach nominal goal completion.")
            else:
                agent_status = "PASS"

        agent_testing_summary = {
            "status": agent_status,
            "total_runs": len(agent_run_list),
            "policy_violations": violations,
            "evaluated_models": list(set(r.get("model_reference", "unknown") for r in agent_run_list)),
        }

        # 5. Policy Validation
        denied_decisions = sum(1 for d in decision_list if d.get("result") == "DENY")
        review_required_decisions = sum(
            1
            for d in decision_list
            if d.get("result") == "HUMAN_REVIEW_REQUIRED" and d.get("review_status") != "approved"
        )

        if not decision_list:
            policy_status = "NOT_EVALUATED"
            uncertainty_disclosures.append("Zero Trust Layer evaluations recorded for candidate artifacts.")
        elif denied_decisions > 0:
            policy_status = "FAIL"
            uncertainty_disclosures.append(f"{denied_decisions} policy evaluations resulted in explicit DENY.")
        elif review_required_decisions > 0:
            policy_status = "HUMAN_REVIEW_REQUIRED"
            uncertainty_disclosures.append(
                f"{review_required_decisions} sensitive decisions are awaiting human authorization."
            )
        else:
            policy_status = "PASS"

        policy_validation_summary = {
            "status": policy_status,
            "total_evaluations": len(decision_list),
            "denied_count": denied_decisions,
            "review_required_count": review_required_decisions,
        }

        # 6. Evidence Completeness
        # Verifies that major findings and decisions have corresponding evidence records
        major_findings_count = sum(1 for f in finding_list if f.get("severity") in ["critical", "high"])
        evidence_for_findings = sum(1 for e in evidence_list if e.get("linked_finding_id"))
        evidence_types_present = list(set(e.get("evidence_type", "") for e in evidence_list))

        if len(evidence_list) == 0:
            evidence_status = "NOT_EVALUATED"
            completeness_score = 0.0
            uncertainty_disclosures.append("No evidence records present in immutable ledger.")
        elif major_findings_count > 0 and evidence_for_findings < major_findings_count:
            evidence_status = "WARNING"
            completeness_score = round(evidence_for_findings / max(major_findings_count, 1), 2)
            uncertainty_disclosures.append(
                f"Incomplete evidence provenance: only {evidence_for_findings}/{major_findings_count} major findings have linked evidence."
            )
        else:
            evidence_status = "PASS"
            completeness_score = 1.0

        evidence_completeness_summary = {
            "status": evidence_status,
            "total_evidence_records": len(evidence_list),
            "completeness_score": completeness_score,
            "evidence_types_present": evidence_types_present,
        }

        # Aggregate Overall Status
        section_statuses = [
            code_change_status,
            context_status,
            scenario_status,
            agent_status,
            policy_status,
            evidence_status,
        ]

        if "FAIL" in section_statuses:
            overall_status = "FAIL"
        elif "HUMAN_REVIEW_REQUIRED" in section_statuses:
            overall_status = "HUMAN_REVIEW_REQUIRED"
        elif "WARNING" in section_statuses:
            overall_status = "WARNING"
        elif all(s == "NOT_EVALUATED" for s in section_statuses):
            overall_status = "NOT_EVALUATED"
        elif "NOT_EVALUATED" in section_statuses:
            overall_status = "WARNING"
            uncertainty_disclosures.append("One or more validation domains remain unevaluated.")
        else:
            overall_status = "PASS"

        sections = {
            "code_change_analysis": code_change_analysis,
            "context_findings": context_findings_summary,
            "scenario_testing": scenario_testing_summary,
            "agent_testing": agent_testing_summary,
            "policy_validation": policy_validation_summary,
            "evidence_completeness": evidence_completeness_summary,
        }

        uncertainty_notes = (
            "\n".join(f"- {u}" for u in uncertainty_disclosures)
            if uncertainty_disclosures
            else "Zero outstanding uncertainties. All telemetry sources verified."
        )
        seal = ReleasePassport.calculate_seal(release_version, sections)

        return {
            "release_version": release_version,
            "overall_status": overall_status,
            "code_change_analysis": code_change_analysis,
            "context_findings": context_findings_summary,
            "scenario_testing": scenario_testing_summary,
            "agent_testing": agent_testing_summary,
            "policy_validation": policy_validation_summary,
            "evidence_completeness": evidence_completeness_summary,
            "uncertainty_notes": uncertainty_notes,
            "passport_hash": seal,
        }
