# Step 2: Code Quality Analysis

**Goal:** Analyze codebase for quality issues, patterns, and standards compliance

## Actions

### 2.1 Perform Code Review
```yaml
# Comprehensive code review including:
# - Architecture and design patterns
# - Code style and conventions
# - Security vulnerabilities
# - Performance considerations
# - Error handling
# - Test coverage

review_scope: comprehensive
review_tools:
  - linting: true
  - security_scan: true
  - performance_analysis: true
  - code_smells: true
```

### 2.2 Check Code Standards
```yaml
# Verify compliance with project coding standards
# Check adherence to SOLID principles
# Verify proper error handling
# Check documentation of complex logic

standards_check:
  - style_guide: true
  - solid_principles: true
  - error_handling: true
  - documentation: true
```

### 2.3 Analyze Test Coverage
```yaml
# Analyze test coverage across codebase
# Identify untested or poorly tested code
# Check test suite health

coverage_analysis:
  - overall_coverage: true
  - critical_path_coverage: true
  - test_health: true
  - untested_modules: true
```

### 2.4 Run Static Analysis
```yaml
# Execute static code analysis tools
# Check for security vulnerabilities
# Check for performance bottlenecks
# Analyze dependencies for vulnerabilities

static_analysis:
  - security_audit: true
  - dependency_check: true
  - performance_profile: true
```

## Success Criteria
- Code review completed across major components
- Standards compliance verified
- Test coverage analyzed and documented
- Static analysis results collected
- Quality issues identified and categorized

## Output

```yaml
# Quality findings summary
code_quality_issues:
  - critical: []
  - high: []
  - medium: []
  - low: []

standards_compliance:
  - compliant: true
  - exceptions: []
  - notes: ""
```

## Next Steps
Proceed to Step 3: Documentation Review
