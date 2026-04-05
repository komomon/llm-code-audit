# Extended Knowledge Base

Authentication patterns, analysis insights, and methodology supplements discovered during AuthScan analyses and **confirmed by the user**.

**Rules:**
- Entries are only added here after explicit user approval
- AuthScan never writes to this file automatically — it presents discoveries in the report for user review
- This file supplements (does NOT replace or modify) the built-in reference files
- Whether to merge entries into main references is the developer's decision
- Loaded alongside built-in references during analysis

## Entry Format

```markdown
### {Pattern/Insight Name}
- **Type:** auth-pattern / datasink / trust-rule-extension / methodology-note
- **Framework/Language:** {info}
- **Search keywords:** `keyword1`, `keyword2`
- **Description:** {what was discovered}
- **Example:**
  ```{language}
  {code}
  ```
- **Source project:** {project_name}
- **Confirmed date:** {date}
```

---

<!-- User-confirmed entries are appended below this line -->
