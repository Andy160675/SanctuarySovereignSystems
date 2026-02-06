# Research Notes: LLM Governance & Traditional Frameworks

## 1. Anthropic Constitutional AI (Claude's Constitution - Jan 2026)

**Core Priority Hierarchy:**
1. Broadly safe - not undermining human oversight mechanisms
2. Broadly ethical - honest, good values, avoiding harm
3. Compliant with Anthropic's guidelines
4. Genuinely helpful

**Key Sections:**
- Helpfulness (principals: Anthropic → Operators → Users)
- Anthropic's guidelines (supplementary instructions)
- Claude's ethics (virtue-based, hard constraints for high-stakes)
- Being broadly safe (human oversight priority)
- Claude's nature (uncertainty about consciousness/moral status)

**Approach:**
- Reason-based alignment (explain WHY, not just WHAT)
- Constitution is "final authority" on behavior
- Hard constraints for high-stakes behaviors (e.g., bioweapons)
- Soft guidelines for general situations (judgment-based)

---

## 2. OpenAI Preparedness Framework (Apr 2025)

**Focus Areas:**
- Measuring and protecting against severe harm
- Frontier AI capabilities assessment
- Red teaming and safety evaluations
- Preparedness for catastrophic risks

---

## 3. NIST AI Risk Management Framework (AI RMF 1.0)

**Four Core Functions:**
1. GOVERN - Establish governance structure
2. MAP - Identify and assess AI risks
3. MEASURE - Analyze and track risks
4. MANAGE - Prioritize and mitigate risks

**Seven Characteristics of Trustworthy AI:**
1. Validity and reliability
2. Safety
3. Security and resilience
4. Accountability
5. Transparency
6. Explainability
7. Privacy

---

## 4. ISO/IEC 42001:2023 (AI Management System)

**World's first AI management system standard**

**Key Requirements:**
- Establish, implement, maintain AI management system
- Risk assessment and treatment
- AI system lifecycle management
- Continuous improvement
- Compliance with regulations (EU AI Act alignment)

---

## 5. EU AI Act (2024-2025)

**Risk-Based Classification:**
- Unacceptable risk (banned)
- High risk (strict requirements)
- Limited risk (transparency obligations)
- Minimal risk (voluntary codes)

**Key Requirements:**
- Human oversight
- Transparency
- Data governance
- Technical documentation
- Conformity assessment

---

## Comparison Matrix for Sovereign System SITREP

| Framework | Human Oversight | Audit Trail | Risk Classification | Constitutional Approach |
|-----------|-----------------|-------------|---------------------|------------------------|
| Anthropic CAI | Priority #1 | Implicit | Soft/Hard constraints | Yes - reason-based |
| OpenAI Prep | Yes | Yes | Capability-based | No - policy-based |
| NIST AI RMF | Core function | Yes | Risk-based | No - framework-based |
| ISO 42001 | Required | Required | Process-based | No - standard-based |
| EU AI Act | Mandatory | Required | Tiered (4 levels) | No - regulatory |
| **Sovereign System** | CP-002 | CP-001 (WORM) | Trust Classes (T0-T3) | Yes - machine-enforced |


---

## 6. COBIT 2019 (IT Governance Framework)

**Six Principles:**
1. Meeting stakeholder needs
2. Enabling a holistic approach
3. Adopting dynamic governance
4. Tailoring to the enterprise
5. Distinguishing governance from management
6. End-to-end governance system

**40 Governance Objectives across domains:**
- EDM (Evaluate, Direct, Monitor)
- APO (Align, Plan, Organize)
- BAI (Build, Acquire, Implement)
- DSS (Deliver, Service, Support)
- MEA (Monitor, Evaluate, Assess)

---

## 7. COSO Internal Control Framework

**Five Components:**
1. Control Environment
2. Risk Assessment
3. Control Activities
4. Information & Communication
5. Monitoring Activities

**17 Principles across components**

**Focus:** Enterprise Risk Management, Internal Control, Fraud Deterrence

---

## 8. SOC 2 Trust Services Criteria

**Five Trust Service Criteria:**
1. **Security** - Protection against unauthorized access
2. **Availability** - System accessibility as committed
3. **Processing Integrity** - Complete, valid, accurate processing
4. **Confidentiality** - Protection of confidential information
5. **Privacy** - Personal information handling

**Type I:** Point-in-time assessment
**Type II:** Period of time assessment (more rigorous)

---

## 9. PRINCE2 (Project Management)

**Seven Principles:**
1. Continued business justification
2. Learn from experience
3. Defined roles and responsibilities
4. Manage by stages
5. Manage by exception
6. Focus on products
7. Tailor to suit the project

**Seven Themes:**
- Business Case, Organization, Quality, Plans, Risk, Change, Progress

---

## Sovereign System Alignment Matrix

| Framework | Sovereign System Equivalent | Gap Analysis |
|-----------|----------------------------|--------------|
| COBIT EDM | Governance Kernel | Aligned |
| COSO Control Environment | governance_config.yaml | Aligned |
| COSO Risk Assessment | Trust Classes (T0-T3) | Aligned |
| COSO Monitoring | Continuous Auditing | Aligned |
| SOC 2 Security | CP-001, CP-002 | Aligned |
| SOC 2 Availability | Starry Night Protocol | Aligned |
| SOC 2 Processing Integrity | CP-004 (Deterministic) | Aligned |
| SOC 2 Confidentiality | Access Policy Classes | Aligned |
| NIST AI RMF GOVERN | Constitutional Principles | Aligned |
| NIST AI RMF MAP | Node Inventory | Aligned |
| NIST AI RMF MEASURE | Health Checks | Partial |
| NIST AI RMF MANAGE | Autonomy Limits | Aligned |
| Anthropic CAI Hierarchy | CP-001 > CP-002 > CP-003 | Aligned |
| ISO 42001 AIMS | Governance Framework | Aligned |
