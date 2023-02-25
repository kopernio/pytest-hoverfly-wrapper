import pathlib
import re

import pytest

pytest_plugins = "pytester"  # pylint: disable=C0103
TEST_DIR = pathlib.Path(__file__).parent.resolve()


@pytest.fixture
def pyfile_source(request):
    """Yields the appropriate pyfile for a test."""
    pyfile_name = re.sub(r"^test_", "", request.node.name) + ".py"
    pyfile_full_path = TEST_DIR / "end_to_end" / "makepyfile_inputs" / pyfile_name
    with open(pyfile_full_path) as file:
        yield file.read()
