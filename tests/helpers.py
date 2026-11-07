import json
import os
import re
from pathlib import Path
from typing import Any

import tomllib
import yaml
from cookiecutter.main import cookiecutter

# TEMPLATE_DIR lets the tests run against a modified copy of the template.
REPO_ROOT = Path(
    os.environ.get("TEMPLATE_DIR", Path(__file__).resolve().parents[1])
)

CI_PROVIDERS = ["github", "gitlab", "both", "none"]
YES_NO = ["yes", "no"]
LICENSES = json.loads((REPO_ROOT / "cookiecutter.json").read_text())[
    "open_source_license"
]

# Same rule as hooks/pre_gen_project.py: importable and a valid PyPI name.
VALID_SLUG = re.compile(r"[a-z_][a-z0-9_]*")


def bake(output_dir: Path, config_file: Path, **context: str) -> Path:
    """Render the template with ``context`` and return the project path."""
    return Path(
        cookiecutter(
            str(REPO_ROOT),
            no_input=True,
            extra_context=context,
            output_dir=str(output_dir),
            config_file=str(config_file),
        )
    )


def load_toml(path: Path) -> dict[str, Any]:
    with path.open("rb") as file:
        return tomllib.load(file)


def load_yaml(path: Path) -> Any:
    return yaml.safe_load(path.read_text())


def load_json(path: Path) -> Any:
    return json.loads(path.read_text())


GITLAB_RESERVED_KEYS = {
    "default",
    "include",
    "stages",
    "variables",
    "workflow",
}


def github_jobs(project: Path) -> set[str]:
    return set(load_yaml(project / ".github" / "workflows" / "ci.yml")["jobs"])


def gitlab_jobs(project: Path) -> set[str]:
    config = load_yaml(project / ".gitlab-ci.yml")
    return {
        key
        for key in config
        if key not in GITLAB_RESERVED_KEYS and not key.startswith(".")
    }


def dependabot_ecosystems(project: Path) -> set[str]:
    config = load_yaml(project / ".github" / "dependabot.yml")
    return {update["package-ecosystem"] for update in config["updates"]}
