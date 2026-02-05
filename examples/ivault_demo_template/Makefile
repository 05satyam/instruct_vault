PY ?= python
IVAULT ?= ivault
PROMPT := examples/ivault_demo_template/prompts/support_reply.prompt.yml
DATASET := examples/ivault_demo_template/datasets/support_cases.jsonl
REPORT := out/report.json

.PHONY: validate eval render run all

validate:
	$(IVAULT) validate examples/ivault_demo_template/prompts

eval:
	$(IVAULT) eval $(PROMPT) --dataset $(DATASET) --report $(REPORT)

render:
	$(IVAULT) render $(PROMPT) --vars '{"ticket_text":"My app crashed.","customer_name":"Sam"}'

run:
	$(PY) examples/ivault_demo_template/app.py

all: validate eval render run
