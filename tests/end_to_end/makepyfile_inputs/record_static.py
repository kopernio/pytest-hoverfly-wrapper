import pytest
import requests

from pytest_hoverfly_wrapper.simulations import StaticSimulation


@pytest.mark.simulated(StaticSimulation(files=["foobar.json"]))
def test_generate(setup_hoverfly):
    proxy_port = setup_hoverfly[1]
    proxies = {
        "http": "http://localhost:{}".format(proxy_port),
        "https": "http://localhost:{}".format(proxy_port),
    }
    r = requests.get("http://google.com", proxies=proxies)
