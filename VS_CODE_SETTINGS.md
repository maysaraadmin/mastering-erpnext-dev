# VS Code Workspace Settings

This file contains recommended VS Code workspace settings for the ERPNext development book project.

## Settings.json Configuration

Copy the following settings to your workspace `.vscode/settings.json` file:

```json
{
    "python.defaultInterpreterPath": "./env/bin/python",
    "python.linting.enabled": true,
    "python.linting.pylintEnabled": true,
    "python.linting.flake8Enabled": true,
    "python.formatting.provider": "black",
    "python.sortImports.args": ["--profile", "black"],
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
        "source.organizeImports": true
    },
    "files.exclude": {
        "**/__pycache__": true,
        "**/*.pyc": true
    },
    "python.testing.pytestEnabled": true,
    "python.testing.unittestEnabled": true,
    "python.testing.pytestArgs": [
        "chapter-15-automated-testing/tests"
    ],
    "markdown.preview.fontSize": 14,
    "markdown.preview.lineHeight": 1.6,
    "files.associations": {
        "*.md": "markdown"
    }
}
```

## Extensions Recommendations

Install these VS Code extensions for optimal development experience:

- Python (Microsoft)
- Pylance (Microsoft)
- Python Docstring Generator
- Black Formatter (Microsoft)
- Pylint
- Flake8
- Markdown All in One
- GitLens
- Bracket Pair Colorizer
- Indent Rainbow

## Workspace Setup

1. Open the project folder in VS Code
2. Copy the settings above to `.vscode/settings.json`
3. Install recommended extensions
4. Reload VS Code to apply settings

## Python Environment

Ensure you have a Python virtual environment set up:

```bash
python -m venv env
source env/bin/activate  # Linux/Mac
# or
env\Scripts\activate     # Windows
pip install -r requirements.txt
```

## Testing Configuration

The workspace is configured to run tests from:
- `chapter-15-automated-testing/tests/`

Use the VS Code testing panel to run and debug tests.
