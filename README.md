# Pytest Hoverfly Wrapper

This `pytest` plugin allows easy integration of Hoverfly into your tests. Hoverfly is a proxy server that can intercept requests and return custom responses. More info on Hoverfly: https://hoverfly.io/

## Installation

Clone the repository and then install using `setup.py`:

```sh
python setup.py install
```
This will also automatically install the plugin's dependencies. Alternatively, install via `pip`:


    pip install pytest-hoverfly-wrapper


Once installation has finished:

  1. Go to https://hoverfly.io/#download
  2. Download the correct package for your operating system
  3. Extract the `hoverfly` and `hoverctl` files and ensure that these are in your PATH.

## Testing
The quickest way is to run tox:
```
pip install tox
tox -e <py35/py36/etc>
```
You can also run in pytest to make use of its debugging tools:
(Assumes you have a virtual environment set up for a compatible Python version - see setup.py for compatible versions)
```
python setup.py install
pytest tests/
```

## Usage example

### Cache responses to external services

Adding the `setup_hoverfly` fixture will stand up a Hoverfly server instance running on port 8500. You can then use this 
as a proxy that saves the responses to any requests make via the proxy. If the test passes, the saved responses will be dumped 
to file, which will be used when the test runs again.

```python
# Enable the fixture explicitly in your tests or conftest.py (not required when using setuptools entry points)
from pytest_hoverfly_wrapper import GeneratedSimulation
import requests
import pytest

@pytest.mark.simulated(GeneratedSimulation(file="some_file.json"))
def test_something(setup_hoverfly):
    proxy_port = setup_hoverfly[1]
    proxies = {
     "http": "http://localhost:{}".format(proxy_port),
     "https": "http://localhost:{}".format(proxy_port),
    }
    requests.get("https://urlwedontwanttospam.com", proxies=proxies)
    
```
After running the test for the first time, you will find a file located at `./test_data/generated/some_file.json`, 
containing all the requests made using the proxy, as well as the responses to them. Upon running the test the second time, 
the test will load the file and attempt to match requests to the list in the file. If a successful match is found, the matching 
response will be served. If not, the request will be made to its original target and the target's response will be served instead.

### Completely fake responses

You can also specify your own custom responses.

```python
# Enable the fixture explicitly in your tests or conftest.py (not required when using setuptools entry points)
from pytest_hoverfly_wrapper import StaticSimulation
import requests
import pytest

@pytest.mark.simulated(StaticSimulation(files=["google_returns_404.json"]))
def test_something(setup_hoverfly):
    proxy_port = setup_hoverfly[1]
    proxies = {
     "http": "http://localhost:{}".format(proxy_port),
     "https": "http://localhost:{}".format(proxy_port),
    }
    r = requests.get("http://google.com", proxies=proxies)
    assert r.status_code == 404
```
Full code is in `sample/`

### Hoverfly crashes
Occasionally, the Hoverfly proxy might crash mid-test. If this happens, the test will raise `HoverflyCrashException`, 
which gives you clarity of why the test failed and can be caught in your testing framework as part of some test retrying 
logic.

### Logging
`pytest-hoverfly-wrapper` uses the in-built `logging` module for logs. To import the logger:
```python
import logging
from pytest_hoverfly_wrapper import LOGGER_NAME
hoverfly_logger = logging.getLogger(LOGGER_NAME)
```
Then customise the logger as necessary.


### Debugging
In all scenarios, when a response is sent by Hoverfly rather than a remote server, that response will have the `Hoverfly-Cache-Served` 
header set. This differentiates the two types of response, and helps debug situations where you think a response is being served by Hoverfly 
but isn't, e.g. when Hoverfly fails to match the request even though you're expecting it to.

At the end of the test, the plugin will create a `network.json` file containing the list of all requests made (and responses received) 
during the test, including parameters and headers.

## Release History

* 0.1.0
    * Initial release
* 0.1.1
    * Updates the description in the PyPi page.
* 0.1.2
    * Create test data directory if it doesn't exist
* 0.1.3
    * Put the bugfix in 0.1.2 in its correct place and remove extraneous plugin.py code
* 0.1.4
    * Fixes broken domain blocking functionality
* 0.2.0
    * Bug fixes and command line option to pass custom parameters to Hoverfly executable command
* 0.3.0
    * Expose Journal API for accessing journal
* 0.3.2
    * Fixes bug where `block_domains` is ignored if a simulation file isn't specified in `StaticSimulation`
* 0.3.3
    * Registers `simulated` marker used by plugin
* 0.4.0
    * Strips `Expires` property from `Set-Cookie` headers in recorded simulations
* 0.4.1
    * Fixes typo in installation instructions

## Meta

For all queries contact Veli Akiner: veli@kopernio.com

Distributed under a modified MIT license. See ``LICENSE`` for more information.

[https://github.com/kopernio/pytest-hoverfly-wrapper](https://github.com/kopernio/pytest-hoverfly-wrapper)

## Contributing

1. Fork it (<https://github.com/yourname/yourproject/fork>)
2. Create your feature branch (`git checkout -b feature/fooBar`)
3. Commit your changes (`git commit -am 'Add some fooBar'`)
4. Push to the branch (`git push origin feature/fooBar`)
5. Create a new Pull Request

