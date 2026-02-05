from instructvault import InstructVault

vault = InstructVault(repo_root=".")
msgs = vault.render(
    "examples/ivault_demo_template/prompts/support_reply.prompt.yml",
    vars={"ticket_text": "My app crashed.", "customer_name": "Sam"},
)

for m in msgs:
    print(m.role)
    print(m.content)
    print()
