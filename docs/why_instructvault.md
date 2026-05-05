# Why InstructVault

Use this document to quickly decide whether InstructVault is the right tool for your team.

## Best fit
- You want prompts versioned in Git and reviewed through normal PRs.
- You need deterministic prompt checks in CI.
- You want reproducible releases pinned by tag or SHA.
- You do not want a hosted prompt registry in the request path.
- Your engineering team is comfortable treating prompts as code artifacts.

## Weak fit
- You want a no-code prompt editor for non-technical users.
- You need built-in online experimentation, analytics, or approval workflows.
- You want a hosted control plane with dashboards and managed collaboration.
- You expect the library to own model calls, tracing, or eval orchestration end to end.

## Quick comparison

| Approach | Best for | Tradeoff |
| --- | --- | --- |
| Prompt strings in app code | Small apps with a few stable prompts | Prompt changes are coupled to application deploys |
| Prompts in a database/admin UI | Non-technical editing and fast live changes | Weaker Git history, reproducibility, and CI discipline |
| Hosted prompt platforms | Managed collaboration and platform workflows | Added vendor dependency and a non-local runtime path |
| InstructVault | Engineering-led teams that want prompt governance in Git | Less suitable for non-technical editing workflows |

## Design boundary
InstructVault is not trying to be a hosted prompt studio. The core promise is narrower:
- Prompts live in Git
- CI validates and evaluates them
- Releases are immutable tags, SHAs, or bundles
- Runtime stays local and framework-agnostic

If your team wants that exact workflow, InstructVault is a strong fit.
