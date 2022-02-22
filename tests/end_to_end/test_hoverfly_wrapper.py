import os

from pytest_hoverfly_wrapper.plugin import TEST_DATA_DIR


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


def test_no_simulation_marker(setup_hoverfly):
    # We should be able to setup Hoverfly without specifying a simulation
    pass


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
