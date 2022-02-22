import json
import os

import pytest
import requests

from pytest_hoverfly_wrapper.plugin import generate_logs


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