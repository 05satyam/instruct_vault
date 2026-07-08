# Editor autocomplete and inline validation

InstructVault publishes a JSON Schema for prompt specs, so editors can offer
autocompletion and inline error highlighting as you write prompts. The schema is
generated from the same Pydantic models used at runtime, so it never drifts from
actual validation.

- Committed copy: [`schemas/prompt.schema.json`](../schemas/prompt.schema.json)
- Regenerate any time: `ivault schema --out schemas/prompt.schema.json`

## VS Code (YAML)

Install the [YAML extension](https://marketplace.visualstudio.com/items?itemName=redhat.vscode-yaml),
then map the schema to your prompt files in `.vscode/settings.json`:

```json
{
  "yaml.schemas": {
    "schemas/prompt.schema.json": ["**/*.prompt.yml", "**/*.prompt.yaml"]
  }
}
```

Or point at the published schema per-file with a modeline at the top of a prompt:

```yaml
# yaml-language-server: $schema=https://raw.githubusercontent.com/05satyam/instruct_vault/main/schemas/prompt.schema.json
spec_version: "1.0"
name: my_prompt
```

## JSON prompt files

Most editors honor the `$schema` key or a file-pattern association pointing at
`schemas/prompt.schema.json`, giving the same autocomplete for `*.prompt.json`.

## JetBrains IDEs

Settings → Languages & Frameworks → Schemas and DTDs → JSON Schema Mappings →
add `schemas/prompt.schema.json` with file patterns `*.prompt.yml`, `*.prompt.yaml`,
`*.prompt.json`.
