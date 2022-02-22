import json
import os
from textwrap import dedent

import pytest
import requests

from pytest_hoverfly_wrapper.plugin import TEST_DATA_DIR, generate_logs
from pytest_hoverfly_wrapper.simulations import template_block_domain_json


def test_raise_hoverflycrashedexc(testdir, pyfile_source):
    """The plugin should raise HoverflyCrashedException when ConnectionError is raised
    while accessing hoverfly."""

    testdir.makepyfile(pyfile_source)
    result = testdir.runpytest()

    assert result.ret == 1

    result.stdout.fnmatch_lines(
        [
            "*raise HoverflyCrashedException*",
        ]
    )


def test_custom_test_data_dir(testdir, pyfile_source):
    """Test creating a custom directory."""

    testdir.makepyfile(pyfile_source)
    result = testdir.runpytest()
    assert result.ret == 0


def test_generate_sim(testdir, pyfile_source):
    """End-to-end test that runs a test once to generate a simulation, and then again to verify it gets used."""

    sim_file = os.path.join(TEST_DATA_DIR, "generated", "foobar.json")
    try:
        os.remove(sim_file)
    except FileNotFoundError:
        pass
    assert not os.path.exists(sim_file)

    # Run a test with the GeneratedSimulation marker to verify we get a simulation file
    testdir.makepyfile(pyfile_source)
    result = testdir.runpytest()
    assert result.ret == 0
    assert os.path.isfile(sim_file)

    # Run the test again, but this time check for the Hoverfly-Cache-Served header, which indicates that the simulation was used.
    assert_cached_response = """    assert r.headers.get("Hoverfly-Cache-Served")"""
    testdir.makepyfile(pyfile_source + assert_cached_response)
    result = testdir.runpytest("-s")
    assert result.ret == 0


def test_record_static(testdir, pyfile_source):
    # Like the last test but for a static simulation with just one file
    sim_file = os.path.join(TEST_DATA_DIR, "static", "foobar.json")
    try:
        os.remove(sim_file)
    except FileNotFoundError:
        pass
    assert not os.path.exists(sim_file)

    # Run a test with the GeneratedSimulation marker to verify we get a simulation file
    testdir.makepyfile(pyfile_source)
    result = testdir.runpytest()
    assert result.ret == 0
    assert os.path.isfile(sim_file)

    # Run the test again, but this time check for the Hoverfly-Cache-Served header, which indicates that the simulation was used.
    assert_cached_response = """    assert r.headers.get("Hoverfly-Cache-Served")"""
    testdir.makepyfile(pyfile_source + assert_cached_response)
    result = testdir.runpytest("-s")
    assert result.ret == 0


def test_existing_static(testdir, pyfile_source):
    """Test static simulation functionality"""
    testdir.makepyfile(pyfile_source)
    result = testdir.runpytest()
    assert result.ret == 0


def test_generate_logs(mocker, tmpdir):
    mock_request = mocker.MagicMock()
    mock_request.node.sensitive = ["sensitive.host"]
    mock_request.node.mode = "simulate"
    mock_journal_api = mocker.MagicMock()
    with open("tests/input.json") as f:
        mock_journal_api.get.return_value = json.load(f)
    log_file = os.path.join(tmpdir.strpath, "network.json")
    # golden path
    generate_logs(request=mock_request, journal_api=mock_journal_api, test_log_directory=tmpdir.strpath)
    assert os.path.isfile(log_file)
    # exception raised if sensitive host isn't cached
    del mock_journal_api.get.return_value["journal"][0]["response"]["headers"]["Hoverfly-Cache-Served"]
    with pytest.raises(AssertionError):
        generate_logs(request=mock_request, journal_api=mock_journal_api, test_log_directory=tmpdir.strpath)

    # useful message dumped if hoverfly crashes during log retrieval
    mock_journal_api.get.side_effect = requests.exceptions.ConnectionError
    generate_logs(request=mock_request, journal_api=mock_journal_api, test_log_directory=tmpdir.strpath)
    with open(log_file) as f:
        assert json.load(f) == {"msg": "Hoverfly crashed while retrieving logs"}


def test_no_simulation_marker(setup_hoverfly):
    # We should be able to setup Hoverfly without specifying a simulation
    pass


def test_template_block_domain_json():
    template_block_domain_json("reddit.com")


def test_marker_registered(testdir, pyfile_source):
    """Make sure that the plugin's markers are registered."""

    # create a temporary pytest test module
    testdir.makepyfile(pyfile_source)

    # run pytest with the following cmd args
    result = testdir.runpytest("--strict")

    assert result.ret == 0


# TODO: end-to-end tests covering:
#  using static sims,
#  recording and using sims,
#  logging output,
#  spying mode,
#  default mode,
#  combining sims,
#  command line parameters,
#  raising exceptions when sensitive host URLs are accessed,
#  unit tests for setup_hoverfly_mode and generate_logs
# crashing hoverfly
