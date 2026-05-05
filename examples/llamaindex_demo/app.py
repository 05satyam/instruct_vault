from __future__ import annotations

from instructvault import InstructVault
from llama_index.core.llms import ChatMessage
from llama_index.llms.openai import OpenAI


def main() -> None:
    vault = InstructVault(repo_root=".")
    messages = vault.render(
        "examples/llamaindex_demo/prompts/support_reply.prompt.yml",
        vars={
            "ticket_text": "My order arrived damaged and I need a replacement.",
            "customer_name": "Ava",
        },
    )

    llm = OpenAI(model="gpt-4o-mini")
    response = llm.chat(
        [ChatMessage(role=message.role, content=message.content) for message in messages]
    )
    print(response.message.content)


if __name__ == "__main__":
    main()
