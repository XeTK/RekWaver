import os
from pathlib import Path
from rekordboxxml.converter import _is_partial
from rekordboxxml.ffmpeg import get_file_info


def test_is_partial_missing(tmp_path):
    target = tmp_path / 'doesnotexist.wav'
    is_p, reason = _is_partial(target, str(target))
    assert is_p
    assert reason == 'missing'


def test_is_partial_empty(tmp_path):
    f = tmp_path / 'empty.wav'
    f.write_bytes(b'')
    is_p, reason = _is_partial(f, str(f))
    assert is_p
    assert reason == 'empty_file'
