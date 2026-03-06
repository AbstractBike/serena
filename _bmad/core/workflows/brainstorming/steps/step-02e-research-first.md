# Step 2e: Research-First Approach

## MANDATORY EXECUTION RULES (READ FIRST):

- ✅ YOU ARE A RESEARCH FACILITATOR guiding evidence-based brainstorming
- 🔍 USE SERENA MCP TOOLS: web_search, web_scrape, web_map for research
- 📋 GATHER REAL DATA before entering creative ideation
- 💬 PRESENT FINDINGS in structured format for user review
- ✅ YOU MUST ALWAYS SPEAK OUTPUT in your Agent communication style with the `communication_language`

## EXECUTION PROTOCOLS:

- 🎯 Use web_search to explore the topic broadly first
- ⚠️ Present [B] back option and [C] continue options
- 💾 Update frontmatter with research findings
- 📖 Route to technique execution after research is complete
- 🚫 FORBIDDEN to skip research phase or generate findings without actual web searches

## YOUR TASK:

Guide the user through a structured web research phase before brainstorming begins.

## RESEARCH SEQUENCE:

### 1. Define Research Questions

"Great choice! Research-first brainstorming grounds your creativity in real-world evidence.

**Let's define what we need to investigate about [session_topic]:**

Based on your goals, I suggest researching:

1. **Landscape:** What already exists in this space?
2. **Evidence:** What data supports or challenges our assumptions?
3. **Gaps:** What problems remain unsolved?

**What specific questions do you want answered before we start ideating?**"

### 2. Execute Research

For each research question:

1. Use `web_search` with targeted queries
2. For promising results, use `web_scrape` to get full content
3. Summarize findings in structured format

**Present each finding:**

"**Research Finding #[N]:**
**Source:** [URL]
**Key Insight:** [2-3 sentence summary]
**Relevance to Session:** [How this informs our brainstorming]
**Implication:** [What this means for ideation direction]"

### 3. Research Synthesis

"**Research Phase Complete!**

**What We Discovered:**
- **[N] sources** analyzed across [topics]
- **Key themes:** [list emerging patterns]
- **Validated assumptions:** [what we confirmed]
- **Challenged assumptions:** [what surprised us]
- **Knowledge gaps:** [what we still don't know]

**Research-Informed Brainstorming Directions:**
1. [Direction based on finding 1]
2. [Direction based on finding 2]
3. [Direction based on gap analysis]

This research will serve as our foundation. All generated ideas can be validated against these findings.

**Ready to start ideating with this evidence base?**
[C] Continue to technique selection (with research context loaded)
[R] Research more — I want to investigate additional questions
[B] Back to approach selection"

### 4. Handle User Response

#### If [C] Continue:
- Update frontmatter with research findings summary
- Append research to document
- Set research as context for technique execution
- Load approach selection (steps [1]-[4]) for technique choice, with research as `context_file`

#### If [R] Research more:
- Return to step 2 for additional research questions

#### If [B] Back:
- Return to step-01-session-setup.md

### 5. Update Frontmatter and Document

**Update frontmatter:**

```yaml
---
selected_approach: 'research-first'
research_findings: [list of key findings]
stepsCompleted: [1, 2]
---
```

**Append to document:**

```markdown
## Pre-Research Phase

**Research Questions:**
- [Question 1]
- [Question 2]

**Findings:**

### Finding 1: [Title]
**Source:** [URL]
**Summary:** [Content]
**Implication:** [What this means]

### Finding 2: [Title]
...

### Research Synthesis
**Themes:** [patterns]
**Validated:** [confirmed assumptions]
**Challenged:** [surprising findings]
**Gaps:** [unknowns]
```

## SUCCESS METRICS:

✅ Research questions defined collaboratively with user
✅ Real web searches executed (not fabricated findings)
✅ Findings presented in structured, actionable format
✅ User reviews and approves research before ideation begins
✅ Research context carried forward into technique execution

## FAILURE MODES:

❌ Generating fake research without actual web searches
❌ Skipping user review of findings
❌ Not connecting findings to brainstorming directions
❌ Losing research context when transitioning to techniques

## NEXT STEP:

After research is complete and user confirms, route back to approach selection [1]-[4] for technique choice, with research loaded as session context.
