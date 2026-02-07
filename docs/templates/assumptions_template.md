# Assumptions Template

## Purpose

This template documents assumptions made during system design, development, and operation. Tracking assumptions is critical for governance and risk management.

## Project Information

- **Project Name**: 
- **Version**: 
- **Date**: 
- **Owner**: 

## Assumptions Log

| ID | Category | Assumption | Rationale | Impact if False | Validation Method | Status | Notes |
|----|----------|------------|-----------|-----------------|-------------------|--------|-------|
| ASM-001 | | | | | | Active/Validated/Invalid | |
| ASM-002 | | | | | | Active/Validated/Invalid | |
| ASM-003 | | | | | | Active/Validated/Invalid | |

## Assumption Categories

### Technical Assumptions
Assumptions about technology, tools, platforms, or technical capabilities.

**Example**: "System will run on Python 3.9 or higher"

### Security Assumptions
Assumptions about security controls, threats, or the security environment.

**Example**: "Infrastructure provided by cloud provider has adequate physical security"

### Operational Assumptions
Assumptions about how the system will be operated, maintained, or supported.

**Example**: "24/7 operations team available for incident response"

### Business Assumptions
Assumptions about business context, requirements, or constraints.

**Example**: "User base will not exceed 10,000 concurrent users"

### Environmental Assumptions
Assumptions about the deployment or operational environment.

**Example**: "Network latency between services will be less than 10ms"

### Dependency Assumptions
Assumptions about external systems, services, or dependencies.

**Example**: "Third-party API will maintain 99.9% uptime"

## Assumption Status Definitions

- **Active**: Assumption is current and not yet validated
- **Validated**: Assumption has been confirmed as correct
- **Invalid**: Assumption proven false, mitigation needed
- **Deprecated**: No longer relevant to current system

## Impact Assessment

### High Impact
If assumption proves false, could cause:
- System failure or critical malfunction
- Security vulnerability
- Major cost overrun
- Significant schedule delay
- Regulatory non-compliance

### Medium Impact
If assumption proves false, could cause:
- Performance degradation
- Minor security concern
- Moderate cost increase
- Some schedule impact
- Workaround required

### Low Impact
If assumption proves false:
- Minor inconvenience
- Easily mitigated
- No significant impact on timeline or cost

## Validation Methods

- **Testing**: Verify through testing
- **Analysis**: Analyze data or documentation
- **Observation**: Monitor in production
- **Expert Review**: Consult with subject matter experts
- **Vendor Confirmation**: Confirm with vendor or supplier

## Assumption Management Process

1. **Identify**: Document new assumptions as they arise
2. **Assess**: Evaluate potential impact if false
3. **Validate**: Plan and execute validation activities
4. **Monitor**: Regularly review active assumptions
5. **Update**: Change status based on validation results
6. **Mitigate**: If invalid, implement mitigation plan

## Critical Assumptions

List assumptions that, if false, would have severe impact:

1. 
2. 
3. 

## Dependencies on Assumptions

Track which system components or decisions depend on specific assumptions:

| Component | Dependent on Assumption ID | Risk if Invalid |
|-----------|---------------------------|-----------------|
| | | |

## Review Schedule

- **Review Frequency**: Monthly or when significant changes occur
- **Next Review Date**: 
- **Review Owner**: 

## Assumptions Related to Compliance

| Assumption ID | Regulation/Standard | Compliance Requirement |
|---------------|--------------------|-----------------------|
| | | |

## Mitigation Plans

For high-impact assumptions that cannot be validated:

| Assumption ID | Mitigation Strategy | Owner | Status |
|---------------|---------------------|-------|--------|
| | | | |

## Approval

- **Prepared By**: 
- **Reviewed By**: 
- **Approved By**: 
- **Approval Date**: 

## Version History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | | | Initial assumptions document |

## References

- Link to related requirements in traceability matrix
- Link to threat model
- Link to phase gate documentation
