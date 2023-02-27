from subprocess import CalledProcessError

import pytest

from pytest_hoverfly_wrapper.download import binaries_valid


@pytest.fixture
def mock_run(mocker):
    return mocker.patch("pytest_hoverfly_wrapper.download.run", autospec=True)


@pytest.fixture
def mock_get_latest_version(mocker):
    mock_obj = mocker.patch("pytest_hoverfly_wrapper.download.get_latest_version", autospec=True)
    mock_obj.return_value = "v1.5.0"
    return mock_obj


@pytest.mark.parametrize("exception", [FileNotFoundError, PermissionError, CalledProcessError(1, "python")])
def test_binaries_valid_fail(mock_run, exception):
    def raise_exc(exc):
        raise exc

    mock_run.side_effect = lambda _, **kw: raise_exc(exception)
    assert not binaries_valid()


def test_binaries_valid_general_exception(mock_run):
    def raise_exc():
        raise Exception

    mock_run.side_effect = lambda _, **kw: raise_exc()
    with pytest.raises(Exception):
        binaries_valid()


def test_binaries_valid_wrong_ver(mock_run, mock_get_latest_version):
    mock_run.return_value.stdout = b"v1.0.0\n"
    mock_run.return_value.returncode = 0
    assert not binaries_valid()


def test_binaries_valid_pass(mock_run, mock_get_latest_version):
    mock_run.return_value.stdout = b"v1.5.0\n"
    mock_run.return_value.returncode = 0
    assert binaries_valid()
