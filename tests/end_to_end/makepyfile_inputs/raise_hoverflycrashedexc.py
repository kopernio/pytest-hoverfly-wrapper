from pytest_hoverfly_wrapper.simulations import GeneratedSimulation
import pytest
import requests


@pytest.mark.simulated(GeneratedSimulation())
def test_sth(setup_hoverfly, mocker):
    mock_obj = mocker.patch("requests.get")
    mock_obj.side_effect = requests.exceptions.ConnectionError
