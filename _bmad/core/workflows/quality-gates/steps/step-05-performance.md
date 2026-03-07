# Step 5: Performance Review

**Goal:** Analyze application performance, identify bottlenecks, and verify performance benchmarks

## Actions

### 5.1 Performance Profiling
```yaml
# Profile application performance under realistic load
# Identify slow operations and bottlenecks
# Measure resource utilization (CPU, memory, I/O)

profiling:
  - load_testing: true
  - resource_monitoring: true
  - bottleneck_analysis: true
  - performance_metrics: true
```

### 5.2 Database Performance
```yaml
# Analyze database queries and operations
# Check for N+1 queries, missing indexes, inefficient patterns

database_performance:
  - query_optimization: true
  - index_analysis: true
  - connection_pooling: true
  - caching_strategy: true
```

### 5.3 API Response Times
```yaml
# Measure and analyze API response times
# Check for slow endpoints and timeouts

api_performance:
  - response_time_analysis: true
  - endpoint_benchmarks: true
  - timeout_handling: true
  - rate_limiting: true
```

### 5.4 Memory Usage
```yaml
# Analyze memory consumption patterns
# Check for memory leaks, excessive allocations

memory_performance:
  - memory_leaks: true
  - allocation_patterns: true
  - garbage_collection: true
  - resource_limits: true
```

### 5.5 Caching Strategy
```yaml
# Review caching implementation and effectiveness
# Check for cache hit rates and optimization opportunities

caching:
  - cache_hit_rate: true
  - cache_strategy: true
  - cache_invalidation: true
  - optimization_opportunities: true
```

## Success Criteria
- Performance profiling completed
- Bottlenecks identified and documented
- Performance benchmarks established
- Optimization opportunities identified

## Output

```yaml
# Performance findings summary
performance_issues:
  - critical: []
  - high: []
  - medium: []
  - low: []

performance_score: 0
benchmarks: []
```

## Next Steps
Proceed to Step 6: Deployment Readiness
