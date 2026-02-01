# CI/CD with InstructVault

## GitHub Actions path filters
You can trigger CI only when prompt-related paths change using `paths` filters in workflow events.

We ship a ready-to-copy workflow at `.github/workflows/ivault.yml`.

## JUnit output
InstructVault can also emit JUnit XML from `ivault eval` via `--junit out/junit.xml`.
