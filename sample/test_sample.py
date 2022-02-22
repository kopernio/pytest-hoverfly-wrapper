import os

import pytest
import requests

from pytest_hoverfly_wrapper import StaticSimulation

pytest_plugins = ["pytest_hoverfly_wrapper"]


@pytest.fixture
def test_data_dir():
    """Overrides the default test data directory"""
    return os.path.join(os.getcwd(), "sample")


@pytest.mark.simulated(StaticSimulation(files=["google_returns_404.json"]))
def test_something(setup_hoverfly):
    proxy_port = setup_hoverfly[1]
    proxies = {
        "http": f"http://localhost:{proxy_port}",
        "https": f"http://localhost:{proxy_port}",
    }
    r = requests.get("http://google.com", proxies=proxies)
    assert r.status_code == 404
