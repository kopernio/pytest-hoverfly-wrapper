import pytest
import requests

from pytest_hoverfly_wrapper.simulations import GeneratedSimulation


@pytest.mark.simulated(GeneratedSimulation(file="foobar.json"))
def test_generate(setup_hoverfly):
    proxy_port = setup_hoverfly[1]
    proxies = {
        "http": "http://localhost:{}".format(proxy_port),
        "https": "http://localhost:{}".format(proxy_port),
    }
    r = requests.get("http://google.com", proxies=proxies)
