from pathlib import Path
import rekordboxxml.converter as conv
import rekordboxxml.ffmpeg as ffmpeg


def test_process_flacs_dry_run(monkeypatch, tmp_path):
    # create fake flac path
    f1 = tmp_path / 'a.flac'
    f1.write_bytes(b'foo')
    # mock get_file_info and get_new_path
    monkeypatch.setattr(ffmpeg, 'get_file_info', lambda p: {'format': {'tags': {'ARTIST': 'A', 'TITLE': 'T', 'ALBUM': ''}}})
    monkeypatch.setattr(conv, 'get_new_path', lambda info, dest: (str(tmp_path), str(tmp_path / 'A-T.wav')))
    updated = conv.process_flacs([str(f1)], destination=str(tmp_path), dry_run=True)
    assert len(updated) == 1
