# AGENTS.md

## Build/Lint/Test Commands

```bash
# Install dependencies
uv sync

# Run tests
uv run python -m pytest tests/
uv run python -m pytest tests/test_setup.py -v
uv run python -m pytest tests/test_model_init.py -v

# Run single test file
uv run python tests/test_setup.py
uv run python tests/test_model_init.py

# Run experiment
uv run python run_experiment.py
uv run python run_experiment.py --phase setup
```

## Code Style Guidelines

- **Python**: >=3.12, use uv package manager
- **Imports**: Group stdlib, third-party, local imports; use `sys.path.insert(0, str(Path(__file__).parent.parent))` for src imports
- **Type hints**: Use `typing` module (Dict, List, Optional, Any)
- **Logging**: Use `logging.getLogger(__name__)` with INFO level
- **Error handling**: Raise descriptive exceptions with context
- **Naming**: snake_case for variables/functions, PascalCase for classes
- **Docstrings**: Triple quotes with Args/Returns documentation
- **Paths**: Use `pathlib.Path` for all file operations
- **Config**: YAML-based with validation via `validate_config()`