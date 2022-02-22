import pytest

pytest_plugins = "pytester"
import re

import pathlib

TEST_DIR = pathlib.Path(__file__).parent.resolve()


@pytest.fixture
def pyfile_source(request):
    """Yields the appropriate pyfile for a test."""
    pyfile_name = re.sub(r"^test_", "", request.node.name) + ".py"
    pyfile_full_path = TEST_DIR / "makepyfile_inputs" / pyfile_name
    with open(pyfile_full_path) as f:
        yield f.read()
