# FivcPlayground Setup Command

## Overview

The `setup` command initializes the FivcPlayground configuration directory structure in your current working directory. It creates the `.fivcplayground/configs/` directory and copies example configuration files from the project.

## Usage

### Basic Setup

```bash
fivcplayground setup
```

This will:
1. Create `.fivcplayground/configs/` directory in your current working directory
2. Copy example configuration files:
   - `agents.yaml.example` → `agents.yaml`
   - `models.yaml.example` → `models.yaml`
   - `embeddings.yaml.example` → `embeddings.yaml`
   - `tools.yaml.example` → `tools.yaml`
3. Prompt for confirmation if files already exist

### Force Overwrite

```bash
fivcplayground setup --force
# or
fivcplayground setup -f
```

Overwrites existing configuration files without prompting.

## Configuration Files

After running setup, you'll have the following configuration files:

### agents.yaml
Defines available agents and their configurations:
- Agent name and ID
- Model to use
- System prompt/backstory
- Description

### models.yaml
Configures LLM providers and models:
- Model provider (OpenAI, Ollama, etc.)
- API keys and endpoints
- Model parameters

### embeddings.yaml
Configures embedding models:
- Embedding provider
- Model selection
- API configuration

### tools.yaml
Configures available tools:
- Tool definitions
- Tool parameters
- Integration settings

## Output

The command provides detailed feedback:

```
╭─ FivcPlayground Setup ─────────────────────────────────────────╮
│ Initializing Configuration                                     │
╰────────────────────────────────────────────────────────────────╯

📁 Created directory: /path/to/.fivcplayground/configs
✅ Copied: agents.yaml
✅ Copied: models.yaml
✅ Copied: embeddings.yaml
✅ Copied: tools.yaml

============================================================
Setup Summary
============================================================
Configuration directory: /path/to/.fivcplayground/configs
Files copied: 4
  • agents.yaml
  • models.yaml
  • embeddings.yaml
  • tools.yaml

Next Steps:
1. Edit configuration files in: /path/to/.fivcplayground/configs
2. Configure your LLM provider (models.yaml)
3. Configure agents (agents.yaml)
4. Configure embeddings (embeddings.yaml)
5. Configure tools (tools.yaml)

✅ Setup completed successfully!
```

## Error Handling

### Missing Source Files
If example configuration files are not found in the project:
```
❌ Error: Project configs directory not found at /path/to/configs
```

### File Copy Errors
If there's an error copying files:
```
❌ Error copying agents.yaml: [error details]
```

## Implementation Details

- **Cross-platform**: Uses `pathlib.Path` for cross-platform path handling
- **Metadata preservation**: Uses `shutil.copy2()` to preserve file metadata
- **Safe overwrite**: Prompts before overwriting existing files (unless `--force` is used)
- **User feedback**: Provides clear status messages and next steps

## Next Steps After Setup

1. Edit the configuration files in `.fivcplayground/configs/`
2. Set your LLM provider credentials in `models.yaml`
3. Configure agents in `agents.yaml`
4. Run FivcPlayground: `fivcplayground run Generic --query "Your query"`

