"""
Phase 1 Determinism Validation
Ensures repeatability and stability of vulnerability detection across multiple runs.
"""

import hashlib
import json
import statistics
from typing import Dict, List, Any
from pathlib import Path


def fingerprint_report(report: Dict[str, Any]) -> str:
    """
    Generate stable hash excluding timestamps and IDs.
    Enables consistent comparison across runs.
    """
    normalized = {
        "findings": [
            {
                "type": f.get("type"),
                "line": f.get("line"),
                "cwe": f.get("cwe"),
                "severity": f.get("severity"),
                "code_snippet": f.get("code_snippet", "")[:100],  # First 100 chars only
            }
            for f in report.get("findings", [])
        ]
    }
    return hashlib.sha256(
        json.dumps(normalized, sort_keys=True).encode()
    ).hexdigest()


def compare_runs(runs: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Compare multiple runs for consistency.
    Returns metrics on finding consistency and CVSS stability.
    """
    if len(runs) < 2:
        return {"error": "At least 2 runs required for comparison"}

    fingerprints = [fingerprint_report(run) for run in runs]
    fingerprint_match = all(fp == fingerprints[0] for fp in fingerprints)

    # Calculate CVSS variance
    cvss_scores = []
    for run in runs:
        for finding in run.get("findings", []):
            cvss = finding.get("cvss_score", 0)
            if cvss:
                cvss_scores.append(cvss)

    cvss_delta = 0
    cvss_variance = 0
    if cvss_scores and len(cvss_scores) >= 2:
        cvss_delta = max(cvss_scores) - min(cvss_scores)
        cvss_variance = statistics.stdev(cvss_scores) if len(cvss_scores) > 1 else 0

    # Analyze finding count consistency
    finding_counts = [len(run.get("findings", [])) for run in runs]
    finding_count_variance = max(finding_counts) - min(finding_counts) if finding_counts else 0

    # Exploit chain consistency
    exploit_chains = [
        run.get("exploit_chain", [])
        for run in runs
    ]
    chains_consistent = all(
        chain == exploit_chains[0] for chain in exploit_chains
    ) if exploit_chains else True

    return {
        "total_runs": len(runs),
        "fingerprint_match": fingerprint_match,
        "finding_count_variance": finding_count_variance,
        "cvss_delta": round(cvss_delta, 2),
        "cvss_variance": round(cvss_variance, 2),
        "exploit_chain_consistent": chains_consistent,
        "fingerprints": fingerprints,
    }


def determine_determinism_status(metrics: Dict[str, Any]) -> str:
    """
    Classify determinism result as PASS, WARN, or FAIL.
    """
    if "error" in metrics:
        return "FAIL"

    if not metrics["fingerprint_match"]:
        return "FAIL"

    if metrics["finding_count_variance"] > 0:
        return "FAIL"

    if metrics["cvss_delta"] > 0.3:
        return "WARN"

    if not metrics["exploit_chain_consistent"]:
        return "WARN"

    return "PASS"


def generate_determinism_report(runs: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Generate comprehensive determinism report.
    """
    metrics = compare_runs(runs)
    status = determine_determinism_status(metrics)

    return {
        "status": status,
        "metrics": metrics,
        "interpretation": {
            "PASS": "Results are highly deterministic and trustworthy",
            "WARN": "Minor inconsistencies detected - review CVSS variance",
            "FAIL": "Non-deterministic behavior - results unreliable",
        }.get(status, "Unknown"),
    }


if __name__ == "__main__":
    # Example usage for testing
    sample_run_1 = {
        "findings": [
            {
                "type": "sql_injection",
                "line": 42,
                "cwe": "CWE-89",
                "severity": "Critical",
                "cvss_score": 9.8,
                "code_snippet": "query = f'SELECT * FROM users WHERE id={user_id}'",
            },
            {
                "type": "xss",
                "line": 105,
                "cwe": "CWE-79",
                "severity": "High",
                "cvss_score": 7.2,
                "code_snippet": "return user_input",
            },
        ]
    }

    sample_run_2 = {
        "findings": [
            {
                "type": "sql_injection",
                "line": 42,
                "cwe": "CWE-89",
                "severity": "Critical",
                "cvss_score": 9.7,
                "code_snippet": "query = f'SELECT * FROM users WHERE id={user_id}'",
            },
            {
                "type": "xss",
                "line": 105,
                "cwe": "CWE-79",
                "severity": "High",
                "cvss_score": 7.3,
                "code_snippet": "return user_input",
            },
        ]
    }

    report = generate_determinism_report([sample_run_1, sample_run_2])
    print(json.dumps(report, indent=2))
