# Drop-in guide (existing CI/CD)

Use this when you already have CI and just want to add prompt checks.

## 1) Add repo conventions
- `prompts/**/*.prompt.yml` or `.prompt.json`
- `datasets/**/*.jsonl`

## 2) Add CLI steps
Run these in your existing pipeline:
```
ivault validate prompts
ivault eval prompts/<prompt>.prompt.yml --report out/report.json --junit out/junit.xml
```

Optional (recommended for production builds):
```
ivault bundle --prompts prompts --out out/ivault.bundle.json --ref <tag-or-sha>
```

## 3) Deploy from tag or bundle
- Use a git tag (e.g., `prompts/v1.3.0`), or
- Ship `out/ivault.bundle.json` with your app

## 4) Add governance
- Add CODEOWNERS for `prompts/`
- Require CI checks for prompt paths
