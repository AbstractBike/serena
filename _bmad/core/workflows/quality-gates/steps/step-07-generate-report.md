# Step 7: Generate Quality Report

**Goal:** Compile all quality gate findings into comprehensive report with actionable recommendations

## Actions

### 7.1 Aggregate Findings
```yaml
# Collect findings from all quality gate steps
# Identify critical issues that block deployment
# Generate prioritized recommendations

findings_aggregation:
  - code_quality: true
  - documentation: true
  - security: true
  - performance: true
  - deployment: true
```

### 7.2 Prioritize Issues
```yaml
# Prioritize issues by severity and impact
# Critical issues: Must block deployment until resolved
# High issues: Should be addressed before next deployment
# Medium/Low issues: Can be deferred to next iteration

prioritization:
  - critical_blocking: true
  - high_priority: true
  - medium_low_deferred: true
  - timeline_estimation: true
```

### 7.3 Generate Recommendations
```yaml
# Create actionable recommendations for each issue
# Link recommendations to best practices and guidelines
# Assign owners and due dates

recommendations:
  - actionable_items: true
  - best_practices: true
  - owner_assignment: true
  - due_dates: true
  - tracking: true
```

### 7.4 Create Quality Report
```yaml
# Generate comprehensive quality gate report
# Include executive summary and detailed findings
# Save report to designated output directory

report_generation:
  - executive_summary: true
  - detailed_findings: true
  - metrics_dashboard: true
  - export_formats: ["markdown", "json", "pdf"]
```

## Success Criteria
- All findings aggregated from quality gate steps
- Issues prioritized by severity and impact
- Comprehensive recommendations generated
- Quality report created and saved

## Output

```yaml
# Quality gate completion summary
quality_gate_summary:
  - total_issues: 0
  - critical_issues: 0
  - high_issues: 0
  - medium_issues: 0
  - low_issues: 0

deployment_decision: pending
next_steps: []
```

## Quality Gate Completion

All quality gates have been executed successfully. The workflow is complete with comprehensive quality analysis, security review, performance evaluation, and deployment readiness assessment. Recommendations have been generated and the quality report is ready for review.

Proceed to review the quality gate findings and make deployment decision.
