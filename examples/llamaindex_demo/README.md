# LlamaIndex demo

Minimal example showing how to render a Git-versioned prompt with InstructVault and send it to a LlamaIndex chat model.

## Requirements
- Python 3.10+
- `OPENAI_API_KEY` set in your environment

## Install
```bash
pip install instructvault llama-index-llms-openai
```

## Validate the prompt
```bash
ivault validate examples/llamaindex_demo/prompts
```

## Run the example
```bash
python examples/llamaindex_demo/app.py
```

## What it does
- Loads `examples/llamaindex_demo/prompts/support_reply.prompt.yml`
- Renders the prompt with runtime variables
- Converts the rendered messages to LlamaIndex `ChatMessage` objects
- Sends the request through `llama_index.llms.openai.OpenAI`

## Optional
To test a different input, edit the `vars` dictionary in `app.py`.
