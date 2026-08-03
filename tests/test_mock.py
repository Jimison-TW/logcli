from unittest.mock import mock_open, patch

from logcli.parser import read_lines


def test_read_lines():
    fake_content = mock_open(read_data="hello\nworld")
    with patch("logcli.parser.open", fake_content):
        assert len(read_lines("不存在.txt")) == 2
