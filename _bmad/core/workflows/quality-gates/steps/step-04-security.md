# Step 4: Security Review

**Goal:** Perform comprehensive security analysis to identify vulnerabilities and ensure best practices

## Actions

### 4.1 Static Security Analysis
```yaml
# Analyze code for common security vulnerabilities
# Check for sensitive data exposure
# Verify authentication and authorization patterns
# Check for input validation and sanitization

static_security_check:
  - sql_injection: true
  - xss_vulnerabilities: true
  - authentication_flaws: true
  - authorization_issues: true
  - input_validation: true
  - data_exposure: true
  - dependency_vulnerabilities: true
```

### 4.2 Secrets Management
```yaml
# Check for hardcoded secrets, API keys, credentials
# Verify proper secrets management
# Check for sensitive data in logs or error messages

secrets_check:
  - hardcoded_secrets: true
  - api_keys: true
  - credentials: true
  - sensitive_logs: true
  - environment_variables: true
```

### 4.3 Dependencies Security
```yaml
# Analyze third-party dependencies for known vulnerabilities
# Check for outdated packages
# Verify dependency versions and updates

dependency_security:
  - known_vulnerabilities: true
  - outdated_packages: true
  - supply_chain: true
  - transitive_dependencies: true
```

### 4.4 Network Security
```yaml
# Check for network-related security issues
# Verify secure communication protocols
# Check for proper certificate validation

network_security:
  - ssl_tls: true
  - certificate_validation: true
  - secure_protocols: true
  - api_security: true
```

### 4.5 Access Control
```yaml
# Review access control mechanisms
# Check authentication and authorization patterns
# Verify proper role-based access control

access_control:
  - authentication: true
  - authorization: true
  - role_based_access: true
  - session_management: true
  - rate_limiting: true
```

## Success Criteria
- Security analysis completed across all categories
- Critical vulnerabilities identified
- Security best practices verified
- Access control mechanisms reviewed

## Output

```yaml
# Security findings summary
security_issues:
  - critical: []
  - high: []
  - medium: []
  - low: []

security_score: 0
recommendations: []
```

## Next Steps
Proceed to Step 5: Performance Review
