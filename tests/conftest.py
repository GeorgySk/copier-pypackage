from collections.abc import Callable
from pathlib import Path

import pytest
from hypothesis import HealthCheck, settings

from helpers import bake, snapshot_template

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
def template_dir(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """The template as it is in the working tree, outside git."""
    return snapshot_template(tmp_path_factory.mktemp("template") / "copy")


@pytest.fixture(scope="session")
def baked(
    tmp_path_factory: pytest.TempPathFactory, template_dir: Path
) -> Callable[..., Path]:
    """Memoized ``bake`` so that tests sharing a context share a render."""
    cache: dict[tuple[tuple[str, object], ...], Path] = {}

    def _baked(**context: object) -> Path:
        key = tuple(sorted(context.items()))
        if key not in cache:
            cache[key] = bake(
                tmp_path_factory.mktemp("bake"), template_dir, **context
            )
        return cache[key]

    return _baked
