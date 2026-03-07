# Step 3: Documentation Review

**Goal:** Verify documentation completeness, accuracy, and accessibility

## Actions

### 3.1 Review Code Documentation
```yaml
# Check for:
# - API documentation completeness
# - Inline code comments
# - README files for all modules
# - Architecture documentation
# - Setup and installation guides

code_docs_check:
  - api_completeness: true
  - inline_comments: true
  - readme_files: true
  - architecture_docs: true
  - setup_guides: true
```

### 3.2 Review User Documentation
```yaml
# Check for:
# - User guides
# - Contribution guidelines
# - Troubleshooting documentation
# - FAQ completeness

user_docs_check:
  - user_guides: true
  - contribution_guidelines: true
  - troubleshooting: true
  - faq_completeness: true
```

### 3.3 Check Documentation Consistency
```yaml
# Verify that code and user documentation are aligned
# Check for outdated information
# Verify consistency across different documentation sections

consistency_check:
  - alignment: true
  - currency: true
  - cross_section_consistency: true
```

### 3.4 Verify Accessibility
```yaml
# Check that documentation is accessible and readable
# Verify proper formatting and structure

accessibility_check:
  - readability: true
  - structure: true
  - formatting: true
  - links_valid: true
```

## Success Criteria
- All documentation sections reviewed
- Coverage gaps identified
- Consistency issues documented
- Accessibility problems addressed

## Output

```yaml
# Documentation quality findings
documentation_issues:
  - critical: []
  - high: []
  - medium: []
  - low: []

completeness_score: 0
consistency_score: 0
accessibility_score: 0
```

## Next Steps
Proceed to Step 4: Security Review
