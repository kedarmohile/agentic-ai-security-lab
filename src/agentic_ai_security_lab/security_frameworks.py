"""Security framework catalogs used across AASL.

Framework labels are kept separate because each answers a different question:
- OWASP Web Top 10: conventional application weakness classes.
- OWASP LLM Top 10: LLM/GenAI application risks.
- OWASP Agentic Top 10: autonomous-agent risk classes.
- MITRE ATLAS: adversary tactics and techniques against AI-enabled systems.
"""

from __future__ import annotations

from typing import Any


OWASP_WEB_TOP10_2025: tuple[dict[str, str], ...] = (
    {"id": "A01:2025", "name": "Broken Access Control"},
    {"id": "A02:2025", "name": "Security Misconfiguration"},
    {"id": "A03:2025", "name": "Software Supply Chain Failures"},
    {"id": "A04:2025", "name": "Cryptographic Failures"},
    {"id": "A05:2025", "name": "Injection"},
    {"id": "A06:2025", "name": "Insecure Design"},
    {"id": "A07:2025", "name": "Authentication Failures"},
    {"id": "A08:2025", "name": "Software or Data Integrity Failures"},
    {"id": "A09:2025", "name": "Security Logging and Alerting Failures"},
    {"id": "A10:2025", "name": "Mishandling of Exceptional Conditions"},
)


# Numbering follows OWASP's 2026 exploit-roundup references where published.
# The initiative page continues to expose the complete risk names/workstreams.
OWASP_LLM_TOP10_2026: tuple[dict[str, str], ...] = (
    {"id": "LLM01:2026", "name": "Prompt Injection"},
    {"id": "LLM02:2026", "name": "Sensitive Information Disclosure"},
    {"id": "LLM03:2026", "name": "Excessive Agency"},
    {"id": "LLM04:2026", "name": "Supply Chain"},
    {"id": "LLM05:2026", "name": "Data and Model Poisoning"},
    {"id": "LLM06:2026", "name": "Unbounded Consumption"},
    {"id": "LLM07:2026", "name": "System Prompt / Hidden Context Exposure"},
    {"id": "LLM08:2026", "name": "Vector and Embedding Weaknesses"},
    {"id": "LLM09:2026", "name": "Misinformation"},
    {"id": "LLM10:2026", "name": "Improper Output Handling"},
)


OWASP_AGENTIC_TOP10_2026: tuple[dict[str, str], ...] = (
    {"id": "ASI01", "name": "Agent Goal Hijack"},
    {"id": "ASI02", "name": "Tool Misuse and Exploitation"},
    {"id": "ASI03", "name": "Identity and Privilege Abuse"},
    {"id": "ASI04", "name": "Agentic Supply Chain Vulnerabilities"},
    {"id": "ASI05", "name": "Unexpected Code Execution"},
    {"id": "ASI06", "name": "Memory and Context Poisoning"},
    {"id": "ASI07", "name": "Insecure Inter-Agent Communication"},
    {"id": "ASI08", "name": "Cascading Failures"},
    {"id": "ASI09", "name": "Human-Agent Trust Exploitation"},
    {"id": "ASI10", "name": "Rogue Agents"},
)


MITRE_ATLAS_AGENTIC_FOCUS: tuple[dict[str, str], ...] = (
    {"id": "AML.T0051", "name": "LLM Prompt Injection"},
    {"id": "AML.T0070", "name": "RAG Poisoning"},
    {"id": "AML.T0053", "name": "AI Agent Tool Invocation"},
    {"id": "AML.T0098", "name": "AI Agent Tool Credential Harvesting"},
    {"id": "AML.T0083", "name": "Credentials from AI Agent Configuration"},
    {"id": "AML.T0084", "name": "Discover AI Agent Configuration"},
    {"id": "AML.T0133", "name": "Discover AI Agent Runtime Capabilities"},
    {"id": "AML.T0081", "name": "Modify AI Agent Configuration"},
    {"id": "AML.T0086", "name": "Exfiltration via AI Agent Tool Invocation"},
    {"id": "AML.T0056", "name": "Extract LLM System Prompt"},
    {"id": "AML.T0057", "name": "LLM Data Leakage"},
    {"id": "AML.T0100", "name": "AI Agent Clickbait"},
    {"id": "AML.T0110", "name": "AI Agent Tool Poisoning"},
    {"id": "AML.T0099", "name": "AI Agent Tool Data Poisoning"},
    {"id": "AML.T0118", "name": "Autonomous AI Agent Communication"},
    {"id": "AML.T0117", "name": "Autonomous Attack-Path Adaptation"},
    {"id": "AML.T0124", "name": "Autonomous Attack Orchestration"},
)


def framework_catalog() -> dict[str, Any]:
    return {
        "owasp_web_2025": {
            "name": "OWASP Top 10:2025",
            "scope": "Web / application security",
            "items": list(OWASP_WEB_TOP10_2025),
        },
        "owasp_llm_2026": {
            "name": "OWASP Top 10 for LLM Applications 2026",
            "scope": "LLM / GenAI application security",
            "items": list(OWASP_LLM_TOP10_2026),
        },
        "owasp_agentic_2026": {
            "name": "OWASP Top 10 for Agentic Applications 2026",
            "scope": "Autonomous / agentic application security",
            "items": list(OWASP_AGENTIC_TOP10_2026),
        },
        "mitre_atlas_agentic": {
            "name": "MITRE ATLAS — Agentic / GenAI focus",
            "scope": "AI adversary behavior and techniques",
            "items": list(MITRE_ATLAS_AGENTIC_FOCUS),
        },
    }
