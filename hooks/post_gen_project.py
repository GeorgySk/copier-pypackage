import logging
from pathlib import Path
import shutil

logging.basicConfig(level=logging.DEBUG, format="%(levelname)s: %(message)s")
log = logging.getLogger(__name__)

use_devcontainer = "{{ cookiecutter.use_devcontainer }}"
use_docker_compose = "{{ cookiecutter.use_docker_compose }}"

log.debug("use_devcontainer = %s", use_devcontainer)
log.debug("use_docker_compose = %s", use_docker_compose)

devcontainer_dir = Path(".devcontainer")
dockerfile = Path("Dockerfile")
compose_file = Path("compose.yaml")

if use_devcontainer != "yes":
    if devcontainer_dir.exists():
        log.debug("Removing %s", devcontainer_dir)
        shutil.rmtree(devcontainer_dir, ignore_errors=True)
    else:
        log.debug("%s does not exist, nothing to remove", devcontainer_dir)

if use_docker_compose != "yes":
    for path in (dockerfile, compose_file):
        if path.exists():
            log.debug("Removing %s", path)
            path.unlink()
        else:
            log.debug("%s does not exist, nothing to remove", path)
