# -*- coding: utf-8 -*-

import glob
import json
import os
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import polling
import pytest
import requests
from dateutil.parser import parse

from .logger import logger
from .simulations import StaticSimulation

BASE_API_URL = "http://localhost:{}/api/v2"
HOVERFLY_API_MODE = f"{BASE_API_URL}/hoverfly/mode"
HOVERFLY_API_SIMULATION = f"{BASE_API_URL}/simulation"
HOVERFLY_API_JOURNAL = f"{BASE_API_URL}/journal"

JOURNAL_LIMIT = 2000

HF_ADMIN_PORT = 8888
PROXY_PORT = 8500


@pytest.fixture
def ignore_hosts(request):
    request.node.ignore = "localhost"


@pytest.fixture
def sensitive_hosts(request):
    # We verify that requests to these hosts in tests are cached in simulations.
    request.node.sensitive = ()


TEST_DATA_DIR = os.path.join(os.getcwd(), "test_data")


@pytest.fixture
def test_data_dir():
    return TEST_DATA_DIR


@pytest.fixture
def _test_data_dir(test_data_dir):
    for dir_ in (test_data_dir, os.path.join(test_data_dir, "static"), os.path.join(test_data_dir, "generated")):
        Path(dir_).mkdir(parents=True, exist_ok=True)
    return test_data_dir


def pytest_addoption(parser):
    parser.addoption(
        "--forcelive",
        action="store_true",
        default=False,
        help="Forces tests using generated simulations to run against live endpoints, and re-record the simulation.",
    )
    parser.addoption(
        "--refreshexpired",
        action="store_true",
        default=False,
        help="Re-records any tests whose generated simulations have expired. Don't use for actual testing.",
    )
    parser.addoption(
        "--hoverfly-opts", action="store", default="", help="Additional arguments to pass to the Hoverfly executable"
    )


@pytest.fixture
def test_log_directory():
    directory = os.path.join("hoverfly_logs")
    if not os.path.exists(directory):
        os.mkdir(directory)
    return directory


def pytest_collection_modifyitems(session, config, items):
    if config.getoption("refreshexpired"):
        # Collect all tests that have expiring simulations
        # (the up-to-date ones get skipped, which is simpler than parsing
        # the simulation files to determine expired status during collection)
        items[:] = [
            item
            for item in items
            if item.get_closest_marker("simulated") and item.get_closest_marker("simulated").args[0].max_age
        ]


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "simulated(simulation_obj): Makes use of recorded responses which are sent in response to web requests "
        "made in tests, rather than receiving responses from their intended targets",
    )


def simulate(file, hf_port, admin_port):
    logger.info("Simulation exists and is up-to-date. Importing.")
    if file:
        with open(file) as f:
            data = f.read().encode("utf-8")
        requests.put(HOVERFLY_API_SIMULATION.format(admin_port), data)
    yield "simulate", hf_port, admin_port


def record(file, node, proxy_port, admin_port, capture_arguments):
    logger.info("Recording a simulation.")
    if not capture_arguments:
        capture_arguments = {"headersWhitelist": ["Cookie"]}
        # TODO: optionally enable this.
        # use these parameters (+ loosening some of the matches) for recording static simulations.
        # capture_arguments = {"headersWhitelist": ["Cookie"], "stateful": True}
    requests.put(HOVERFLY_API_MODE.format(admin_port), json={"mode": "capture", "arguments": capture_arguments})
    yield "record", proxy_port, admin_port
    if hasattr(node, "dont_save_sim"):
        logger.info("Test did not pass, not saving simulation")
        return

    sim = requests.get(HOVERFLY_API_SIMULATION.format(admin_port)).text

    data = json.loads(sim)
    new_pairs = []
    hosts_to_ignore = [node.ignore] if isinstance(node.ignore, str) else node.ignore
    for pair in data["data"]["pairs"]:
        # Remove expiry from Set-Cookie headers in Hoverfly responses
        set_cookie_header = pair["response"]["headers"].get("Set-Cookie", [])
        set_cookie_header[:] = [re.sub(r"(E|e)xpires=[^;]+;*", "", c) for c in set_cookie_header]
        # Allow us to differentiate cached responses from proxied ones.
        pair["response"]["headers"]["Hoverfly-Cache-Served"] = ["True"]
        # `value` is a URL
        if not any(host in pair["request"]["destination"][0]["value"] for host in hosts_to_ignore):
            new_pairs.append(pair)
    data["data"]["pairs"] = new_pairs
    with open(file, "w") as f:
        f.write(json.dumps(data, indent=4, separators=(",", ": ")))


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    yield
    if call.when == "call" and call.excinfo:
        item.dont_save_sim = True


@pytest.fixture
def setup_hoverfly(request, hf_ports, test_log_directory, ignore_hosts, sensitive_hosts, _test_data_dir):
    # Start Hoverfly
    logger.info("Setting up hoverfly")
    port, admin_port = hf_ports
    if not hasattr(request.config, "slaveinput"):
        # Cleaning up any running hoverctl processes is nice, but too risky in distributed mode
        subprocess.Popen(["hoverctl", "stop"], stdout=subprocess.PIPE, stderr=subprocess.PIPE).wait()

    logger.info("Starting hoverfly")
    add_opts = request.config.getoption("hoverfly_opts")
    hoverfly_cmd = ["hoverfly", "-pp", str(port), "-ap", str(admin_port), *add_opts.split()]
    exc = None
    with open(os.path.join(test_log_directory, "hoverfly.log"), "w") as f:
        for _ in range(3):
            hf_proc = subprocess.Popen(hoverfly_cmd, stdout=f, stderr=f)
            try:
                polling.poll(
                    target=lambda: requests.get(HOVERFLY_API_MODE.format(admin_port)).status_code == 200,
                    step=0.2,
                    timeout=5,
                    ignore_exceptions=requests.exceptions.ConnectionError,
                )
                break
            except polling.TimeoutException as e:
                exc = e
                subprocess.Popen(["ps", "-ef"], stdout=f, stderr=f).wait()
        else:
            raise exc

    requests.put(HOVERFLY_API_MODE.format(admin_port), json={"mode": "spy"})

    try:
        yield from setup_hoverfly_mode(request, port, admin_port, _test_data_dir)
        generate_logs(request, JournalAPI(admin_port=hf_ports[1]), test_log_directory)
    finally:
        logger.warning("Killing hoverfly")
        hf_proc.kill()
        logger.warning("Killed hoverfly")


def setup_hoverfly_mode(request, port, admin_port, data_dir):
    sim_marker = request.node.get_closest_marker("simulated")
    sim_config = StaticSimulation() if not sim_marker else sim_marker.args[0]
    file = sim_config.full_file_path(data_dir, admin_port)
    if no_valid_simulation_exists(request, file, sim_config.max_age):
        request.node.mode = "record"
        yield from record(file, request.node, port, admin_port, sim_config.capture_config)
    else:
        request.node.mode = "simulate"
        logger.info("Loading file: %s", file)
        yield from simulate(file, port, admin_port)


def no_valid_simulation_exists(request, sim_file, max_age_seconds):
    if request.config.getoption("forcelive"):
        return True
    try:
        with open(sim_file) as f:
            sim_metadata = json.loads(f.read())["meta"]
            date_sim_created = parse(sim_metadata.get("timeExported"))
            age = (datetime.now(timezone.utc) - date_sim_created).total_seconds()
            if request.config.getoption("refreshexpired"):
                if max_age_seconds and age > max_age_seconds:
                    logger.debug("Simulation is expired.")
                    return True
                else:
                    skip_msg = "Simulation up-to-date. No need to run test."
                    logger.warning(skip_msg)
                    pytest.skip(skip_msg)
    except FileNotFoundError:
        logger.debug("No simulation file found.")
        return True
    return False


@pytest.fixture
def hf_ports(request):
    """Sets a unique port for each worker thread to talk to its instance of hoverfly."""
    if hasattr(request.config, "slaveinput"):
        increment = int(request.config.slaveinput["slaveid"][-1])
    else:
        increment = 0
    admin_port = HF_ADMIN_PORT + increment
    request.config.admin_port = admin_port
    return PROXY_PORT + increment, admin_port


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_call(item):
    outcome = yield
    if "setup_hoverfly" not in item.fixturenames:
        return
    try:
        requests.get(f"http://localhost:{item.config.admin_port}")
    except requests.exceptions.ConnectionError:
        logger.warning("Hoverfly crashed.")
        try:
            requests.get(f"http://localhost:{item.config.admin_port}")
        except requests.exceptions.ConnectionError:

            def raise_hoverfly_exception():
                raise HoverflyCrashedException("Hoverfly crashed")

            outcome.get_result = raise_hoverfly_exception


def generate_logs(request, journal_api, test_log_directory):
    network_log_file = os.path.join(test_log_directory, "network.json")
    with open(network_log_file, "w") as f:
        logger.warning("Getting journal")
        try:
            loaded_journal = journal_api.get()
        except requests.exceptions.ConnectionError:
            logger.warning("Hoverfly fell over. No network log available")
            f.write(json.dumps({"msg": "Hoverfly crashed while retrieving logs"}))
            return
        logger.warning("Got journal")
        try:
            for pair in loaded_journal["journal"]:
                # Truncate long responses, particularly PDF ones. We're not usually interested in the data itself.
                if len(pair["response"]["body"]) > 1000:
                    pair["response"]["body"] = pair["response"]["body"][:1000] + "...<truncated>"
                if request.node.mode == "simulate" and any(
                    host in pair["request"]["destination"] for host in request.node.sensitive
                ):
                    assert pair["response"]["headers"].get(
                        "Hoverfly-Cache-Served"
                    ), f"Warning: sensitive URL is being hit in a simulated test: {pair['request']}"
        finally:
            f.write(json.dumps(loaded_journal, indent=4, separators=(",", ": ")))


class JournalAPI:
    def __init__(self, admin_port):
        self.admin_port = admin_port

    def delete(self):
        requests.delete(HOVERFLY_API_JOURNAL.format(self.admin_port))

    def get(self):
        offset = 0
        journals_per_request = 10

        def get_running_journal():
            return json.loads(
                requests.get(
                    HOVERFLY_API_JOURNAL.format(self.admin_port) + f"?limit={journals_per_request}&offset={offset}"
                ).text
            )

        running_journal = get_running_journal()
        while running_journal["total"] > len(running_journal["journal"]):
            hf_journal = get_running_journal()
            running_journal["journal"] += hf_journal["journal"]
            offset += journals_per_request
        return running_journal


@pytest.fixture
def journal_api(setup_hoverfly):
    return JournalAPI(setup_hoverfly[2])


def pytest_unconfigure(config):
    for file in glob.glob("combined_temp*.json"):
        os.remove(file)


class HoverflyCrashedException(Exception):
    pass
