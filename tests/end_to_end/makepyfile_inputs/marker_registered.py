import pytest
import requests

from pytest_hoverfly_wrapper.simulations import GeneratedSimulation


@pytest.mark.simulated(GeneratedSimulation())
def test_sth(setup_hoverfly, mocker):
    pass
