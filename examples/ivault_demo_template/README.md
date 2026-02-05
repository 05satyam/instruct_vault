# InstructVault demo template

Minimal, end-to-end example you can copy into an existing repo.

## Contents
- `prompts/support_reply.prompt.yml` — sample prompt with inline test
- `datasets/support_cases.jsonl` — dataset-driven eval rows
- `app.py` — runtime render example

## Quickstart
```bash
# from repo root
pip install instructvault

# validate + eval
ivault validate examples/ivault_demo_template/prompts
ivault eval examples/ivault_demo_template/prompts/support_reply.prompt.yml \
  --dataset examples/ivault_demo_template/datasets/support_cases.jsonl \
  --report out/report.json

# render locally
ivault render examples/ivault_demo_template/prompts/support_reply.prompt.yml \
  --vars '{"ticket_text":"My app crashed.","customer_name":"Sam"}'

# run runtime example
python examples/ivault_demo_template/app.py
```

## Makefile shortcuts
```bash
make -C examples/ivault_demo_template all
```

## Using tags or bundles
```bash
# tag prompts
git add examples/ivault_demo_template/prompts examples/ivault_demo_template/datasets
git commit -m "add ivault demo prompts"
git tag prompts/v1.0.0

# bundle
ivault bundle --prompts examples/ivault_demo_template/prompts \
  --out out/ivault.bundle.json --ref prompts/v1.0.0
```
