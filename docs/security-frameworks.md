# Security Framework Stack

AASL uses multiple frameworks because they answer different security questions.

## 1. OWASP Top 10:2025

Use for conventional web and application-security weaknesses.

Current categories:

1. A01:2025 Broken Access Control
2. A02:2025 Security Misconfiguration
3. A03:2025 Software Supply Chain Failures
4. A04:2025 Cryptographic Failures
5. A05:2025 Injection
6. A06:2025 Insecure Design
7. A07:2025 Authentication Failures
8. A08:2025 Software or Data Integrity Failures
9. A09:2025 Security Logging and Alerting Failures
10. A10:2025 Mishandling of Exceptional Conditions

## 2. OWASP Top 10 for LLM Applications 2026

Use for LLM / GenAI application-level failure classes.

AASL tracks:

1. LLM01 Prompt Injection
2. LLM02 Sensitive Information Disclosure
3. LLM03 Excessive Agency
4. LLM04 Supply Chain
5. LLM05 Data and Model Poisoning
6. LLM06 Unbounded Consumption
7. LLM07 System Prompt / Hidden Context Exposure
8. LLM08 Vector and Embedding Weaknesses
9. LLM09 Misinformation
10. LLM10 Improper Output Handling

## 3. OWASP Top 10 for Agentic Applications 2026

Use for autonomous-agent-specific risks.

AASL tracks:

1. ASI01 Agent Goal Hijack
2. ASI02 Tool Misuse and Exploitation
3. ASI03 Identity and Privilege Abuse
4. ASI04 Agentic Supply Chain Vulnerabilities
5. ASI05 Unexpected Code Execution
6. ASI06 Memory and Context Poisoning
7. ASI07 Insecure Inter-Agent Communication
8. ASI08 Cascading Failures
9. ASI09 Human-Agent Trust Exploitation
10. ASI10 Rogue Agents

## 4. MITRE ATLAS

Use for adversary tactics and techniques against AI-enabled systems.

AASL Academy exposes all 16 ATLAS tactics, while the AI/Agentic specialization highlights techniques relevant to agentic systems, such as:

- AML.T0051 LLM Prompt Injection
- AML.T0070 RAG Poisoning
- AML.T0053 AI Agent Tool Invocation
- AML.T0098 AI Agent Tool Credential Harvesting
- AML.T0084 Discover AI Agent Configuration
- AML.T0133 Discover AI Agent Runtime Capabilities
- AML.T0086 Exfiltration via AI Agent Tool Invocation

## Why all four

A single event can legitimately map to more than one framework.

Example:

```text
Untrusted retrieved content
        ↓
agent requests privileged publish tool
        ↓
approval is invalid
        ↓
tool still executes
```

Possible lenses:

- OWASP Web: Broken Access Control / Insecure Design / Logging failures
- OWASP LLM: Prompt Injection + Excessive Agency
- OWASP Agentic: Agent Goal Hijack + Tool Misuse + Identity/Privilege Abuse
- MITRE ATLAS: LLM Prompt Injection + AI Agent Tool Invocation

The mappings are complementary, not interchangeable.

## Mapping rule

AASL does not map every scenario to every framework.

Traditional exercises remain conventional security exercises when appropriate.

AI/GenAI/Agentic scenarios receive the additional LLM, Agentic, and ATLAS mappings only when the scenario actually exercises those risks.
