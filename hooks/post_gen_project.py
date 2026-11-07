import logging
import shutil
from pathlib import Path

logging.basicConfig(level=logging.DEBUG, format="%(levelname)s: %(message)s")
log = logging.getLogger(__name__)

use_devcontainer = "{{ cookiecutter.use_devcontainer }}"
use_docker_compose = "{{ cookiecutter.use_docker_compose }}"
ci_provider = "{{ cookiecutter.ci_provider }}"

log.debug("use_devcontainer = %s", use_devcontainer)
log.debug("use_docker_compose = %s", use_docker_compose)
log.debug("ci_provider = %s", ci_provider)

devcontainer_dir = Path(".devcontainer")
dockerfile = Path("Dockerfile")
compose_file = Path("compose.yaml")
env_file = Path(".env")  # only holds Docker build args
github_dir = Path(".github")
github_workflows_dir = github_dir / "workflows"
gitlab_ci_file = Path(".gitlab-ci.yml")


def remove(path: Path) -> None:
    if path.is_dir():
        log.debug("Removing %s", path)
        shutil.rmtree(path, ignore_errors=True)
    elif path.exists():
        log.debug("Removing %s", path)
        path.unlink()
    else:
        log.debug("%s does not exist, nothing to remove", path)


if use_devcontainer != "yes":
    remove(devcontainer_dir)

if use_docker_compose != "yes":
    for path in (dockerfile, compose_file, env_file):
        remove(path)

if ci_provider == "github":
    remove(gitlab_ci_file)
elif ci_provider == "gitlab":
    # Dependabot only runs on GitHub, so nothing in .github/ is useful here
    remove(github_dir)
elif ci_provider == "none":
    remove(gitlab_ci_file)
    remove(github_workflows_dir)
