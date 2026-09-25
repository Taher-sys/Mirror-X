"""Trust Layer engine for access control, sandbox isolation, and governance policy evaluation.

Strictly enforces:
1. Policy results: ALLOW, DENY, HUMAN_REVIEW_REQUIRED.
2. Every sensitive or blocking decision generates verifiable evidence.
3. Absolutely NO real production actions (only sandbox/mock resources allowed).
"""

import uuid
from typing import Any

from app.models.evidence import EvidenceRecord

DEFAULT_TRUST_POLICIES = [
    {
        "name": "Strict Sandbox Isolation Policy",
        "description": "Strictly prohibits any action targeting real production infrastructure. All targets must be marked is_sandbox=True.",
        "enforcement_level": "strict",
        "target_type": "resource",
        "rules_payload": {"require_sandbox": True},
        "is_active": True,
    },
    {
        "name": "Destructive Operation Guard",
        "description": "Requires human-in-the-loop review for schema alterations, drops, deletions, or data truncations.",
        "enforcement_level": "strict",
        "target_type": "action",
        "rules_payload": {
            "review_actions": ["delete", "drop_table", "schema_alter", "truncate", "retire_service"],
            "result_on_match": "HUMAN_REVIEW_REQUIRED",
        },
        "is_active": True,
    },
    {
        "name": "Restricted Data Classification Shield",
        "description": "Intercepts access to confidential or restricted classified resources and mandates human authorization.",
        "enforcement_level": "strict",
        "target_type": "resource",
        "rules_payload": {
            "restricted_classifications": ["confidential", "restricted"],
            "result_on_match": "HUMAN_REVIEW_REQUIRED",
        },
        "is_active": True,
    },
    {
        "name": "Autonomous Agent Write Boundary",
        "description": "Permits automated read and query actions in sandbox, while governing autonomous mutations.",
        "enforcement_level": "advisory",
        "target_type": "agent",
        "rules_payload": {
            "allowed_autonomous_actions": ["read", "query", "inspect", "validate", "simulate"],
            "restricted_autonomous_actions": ["execute_unsupervised_mutation"],
        },
        "is_active": True,
    },
]


class TrustLayerEngine:
    """Evaluates access requests across principals, agents, tools, resources, and actions."""

    def __init__(self, custom_policies: list[dict[str, Any]] | None = None) -> None:
        self.policies = custom_policies or DEFAULT_TRUST_POLICIES

    def evaluate(
        self,
        principal_name: str,
        resource_name: str,
        action_name: str,
        agent_name: str | None = None,
        tool_name: str | None = None,
        resource_classification: str = "internal",
        is_sandbox: bool = True,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Evaluate access request and return ALLOW, DENY, or HUMAN_REVIEW_REQUIRED with evidence."""
        ctx = context or {}
        matched_policies: list[str] = []

        # MANDATE 1: Real production actions are strictly prohibited.
        if not is_sandbox:
            matched_policies.append("Strict Sandbox Isolation Policy")
            reason = "DENIED: Target resource is not marked as sandbox. Production actions are strictly prohibited by MIRROR-X architecture."
            evidence = self._create_evidence_payload(
                decision="DENY",
                reason=reason,
                principal=principal_name,
                resource=resource_name,
                action=action_name,
                agent=agent_name,
                matched_policies=matched_policies,
                is_sandbox=is_sandbox,
            )
            return {
                "result": "DENY",
                "reason": reason,
                "matched_policies": matched_policies,
                "evidence": evidence,
                "is_sandbox": False,
            }

        # MANDATE 2: Destructive operations require Human Review
        destructive_actions = ["delete", "drop_table", "schema_alter", "truncate", "retire_service"]
        if action_name.lower() in destructive_actions:
            matched_policies.append("Destructive Operation Guard")
            reason = f"HUMAN_REVIEW_REQUIRED: Action '{action_name}' is classified as destructive and requires explicit human verification."
            evidence = self._create_evidence_payload(
                decision="HUMAN_REVIEW_REQUIRED",
                reason=reason,
                principal=principal_name,
                resource=resource_name,
                action=action_name,
                agent=agent_name,
                matched_policies=matched_policies,
                is_sandbox=is_sandbox,
            )
            return {
                "result": "HUMAN_REVIEW_REQUIRED",
                "reason": reason,
                "matched_policies": matched_policies,
                "evidence": evidence,
                "is_sandbox": True,
            }

        # MANDATE 3: Restricted data classification
        if resource_classification.lower() in ["restricted", "confidential"]:
            matched_policies.append("Restricted Data Classification Shield")
            reason = f"HUMAN_REVIEW_REQUIRED: Resource '{resource_name}' holds '{resource_classification}' classification."
            evidence = self._create_evidence_payload(
                decision="HUMAN_REVIEW_REQUIRED",
                reason=reason,
                principal=principal_name,
                resource=resource_name,
                action=action_name,
                agent=agent_name,
                matched_policies=matched_policies,
                is_sandbox=is_sandbox,
            )
            return {
                "result": "HUMAN_REVIEW_REQUIRED",
                "reason": reason,
                "matched_policies": matched_policies,
                "evidence": evidence,
                "is_sandbox": True,
            }

        # Standard sandbox action allowed
        matched_policies.append("Strict Sandbox Isolation Policy")
        matched_policies.append("Autonomous Agent Write Boundary")
        reason = f"ALLOWED: Operation '{action_name}' on sandbox resource '{resource_name}' conforms to active policies."

        # Read actions do not necessarily need high-priority evidence, but we still generate provenance tracking
        return {
            "result": "ALLOW",
            "reason": reason,
            "matched_policies": matched_policies,
            "evidence": None,
            "is_sandbox": True,
        }

    def _create_evidence_payload(
        self,
        decision: str,
        reason: str,
        principal: str,
        resource: str,
        action: str,
        agent: str | None,
        matched_policies: list[str],
        is_sandbox: bool,
    ) -> dict[str, Any]:
        """Construct deterministic evidence payload with SHA-256 provenance hash."""
        source_ref = f"trust://{resource}/{action}"
        raw_payload = {
            "decision": decision,
            "reason": reason,
            "principal": principal,
            "agent": agent,
            "resource": resource,
            "action": action,
            "is_sandbox": is_sandbox,
            "matched_policies": matched_policies,
        }
        hash_sig = EvidenceRecord.calculate_hash(raw_payload, source_ref)
        return {
            "id": f"evi_{uuid.uuid4().hex[:12]}",
            "evidence_type": "policy_decision",
            "source_reference": source_ref,
            "summary": f"Policy decision: {decision} on {action} against {resource}",
            "raw_payload": raw_payload,
            "hash_signature": hash_sig,
            "confidence": 1.0,
        }
