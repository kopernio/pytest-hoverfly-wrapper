import json
import os

import pytest
import requests

from pytest_hoverfly_wrapper.plugin import generate_logs


@pytest.fixture
def mock_journal_api(mocker):
    return mocker.MagicMock()


@pytest.fixture
def mock_request(mocker):
    mock_request_ = mocker.MagicMock()
    mock_request_.node.sensitive = ["sensitive.host"]
    mock_request_.node.mode = "simulate"
    return mock_request_


@pytest.fixture
def log_file(tmpdir):
    return os.path.join(tmpdir.strpath, "network.json")


def test_generate_logs(mock_request, tmpdir, mock_journal_api, log_file):
    """Golden path"""
    with open("tests/input.json") as f:
        mock_journal_api.get.return_value = json.load(f)
    generate_logs(request=mock_request, journal_api=mock_journal_api, test_log_directory=tmpdir.strpath)
    assert os.path.isfile(log_file)


def test_sensitive_hosts_checked(tmpdir, mock_request, mock_journal_api):
    """Exception raised if sensitive host isn't cached"""
    with open("tests/input.json") as f:
        mock_journal_api.get.return_value = json.load(f)
    del mock_journal_api.get.return_value["journal"][0]["response"]["headers"]["Hoverfly-Cache-Served"]
    with pytest.raises(AssertionError):
        generate_logs(request=mock_request, journal_api=mock_journal_api, test_log_directory=tmpdir.strpath)


def test_log_crash(tmpdir, log_file, mock_request, mock_journal_api):
    """Useful message dumped if hoverfly crashes during log retrieval"""
    mock_journal_api.get.side_effect = requests.exceptions.ConnectionError
    generate_logs(request=mock_request, journal_api=mock_journal_api, test_log_directory=tmpdir.strpath)
    with open(log_file) as f:
        assert json.load(f) == {"msg": "Hoverfly crashed while retrieving logs"}
