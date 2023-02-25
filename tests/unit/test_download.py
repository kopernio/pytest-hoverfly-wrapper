from pytest_hoverfly_wrapper.download import binaries_valid
import pytest


@pytest.fixture
def mock_run(mocker):
    return mocker.patch('pytest_hoverfly_wrapper.download.run', autospec=True)


@pytest.mark.parametrize("exception", [FileNotFoundError, PermissionError])
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


def test_binaries_valid_wrong_ver(mock_run):
    mock_run.return_value.stdout = b'v1.0.0\n'
    mock_run.return_value.returncode = 0
    assert not binaries_valid()


def test_binaries_valid_pass(mock_run):
    mock_run.return_value.stdout = b'v2.0.0\n'
    mock_run.return_value.returncode = 0
    assert binaries_valid()


def test_binaries_valid_exec_fail(mock_run):
    mock_run.return_value.returncode = 1
    assert not binaries_valid()
