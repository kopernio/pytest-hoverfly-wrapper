import pytest
import requests

from pytest_hoverfly_wrapper.simulations import GeneratedSimulation


@pytest.fixture
def test_data_dir():
    return "./this/dir/structure/doesnt/exist"


@pytest.mark.simulated(GeneratedSimulation())
def test_sth(setup_hoverfly):
    pass
