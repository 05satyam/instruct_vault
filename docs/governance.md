# Governance patterns (enterprise)

## Recommended setup
1) Keep prompts as files in Git: `prompts/**`
2) Add CODEOWNERS for the prompt directory
3) Enable branch protection:
   - require PR reviews
   - require status checks (ivault workflow)
4) Release prompts as tags (e.g., `prompts/v1.2.0`)
5) Deploy by tag/SHA for reproducibility
