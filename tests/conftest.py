from collections.abc import Callable
from pathlib import Path

import pytest
import yaml
from hypothesis import HealthCheck, settings

from helpers import bake

# Rendering the template takes a few hundred milliseconds per example.
settings.register_profile(
    "default",
    deadline=None,
    max_examples=30,
    suppress_health_check=[HealthCheck.too_slow],
)
settings.register_profile(
    "ci",
    deadline=None,
    max_examples=200,
    suppress_health_check=[HealthCheck.too_slow],
)


@pytest.fixture(scope="session")
def cookiecutter_config(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Config file that keeps cookiecutter's replay and cache out of ~."""
    base = tmp_path_factory.mktemp("cookiecutter-home")
    config = base / "config.yaml"
    config.write_text(
        yaml.safe_dump(
            {
                "cookiecutters_dir": str(base / "cookiecutters"),
                "replay_dir": str(base / "replay"),
            }
        )
    )
    return config


@pytest.fixture(scope="session")
def baked(
    tmp_path_factory: pytest.TempPathFactory, cookiecutter_config: Path
) -> Callable[..., Path]:
    """Memoized ``bake`` so that tests sharing a context share a render."""
    cache: dict[tuple[tuple[str, str], ...], Path] = {}

    def _baked(**context: str) -> Path:
        key = tuple(sorted(context.items()))
        if key not in cache:
            cache[key] = bake(
                tmp_path_factory.mktemp("bake"), cookiecutter_config, **context
            )
        return cache[key]

    return _baked
