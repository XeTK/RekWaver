from subprocess import CompletedProcess

import rekwaver.ffmpeg as ffmpeg


def fake_completed(stdout="{}", stderr="", returncode=0):
    return CompletedProcess(
        args=["ffprobe"], returncode=returncode, stdout=stdout, stderr=stderr
    )


def test_get_file_info_success(monkeypatch):
    monkeypatch.setattr(
        ffmpeg,
        "run",
        lambda cmd, capture_output, text: fake_completed(
            '{"format": {"duration": "1.0"}}'
        ),
    )
    info = ffmpeg.get_file_info("/tmp/foo.flac")
    assert "format" in info


def test_get_file_info_failure(monkeypatch):
    monkeypatch.setattr(
        ffmpeg,
        "run",
        lambda cmd, capture_output, text: fake_completed("", "error", returncode=1),
    )
    try:
        ffmpeg.get_file_info("/tmp/bad.flac")
        assert False, "Expected RuntimeError"
    except RuntimeError:
        pass


def test_flac_to_wav_success(monkeypatch, tmp_path):
    # simulate ffmpeg success
    monkeypatch.setattr(
        ffmpeg, "run", lambda cmd, capture_output, text: fake_completed()
    )
    in_f = tmp_path / "in.flac"
    out_f = tmp_path / "out.wav"
    in_f.write_bytes(b"fake")
    ok = ffmpeg.flac_to_wav(str(in_f), str(out_f))
    assert ok is True


def test_flac_to_wav_failure_removes_partial(monkeypatch, tmp_path):
    # simulate ffmpeg failure
    monkeypatch.setattr(
        ffmpeg,
        "run",
        lambda cmd, capture_output, text: fake_completed("", "err", returncode=1),
    )
    in_f = tmp_path / "in.flac"
    out_f = tmp_path / "out.wav"
    in_f.write_bytes(b"fake")
    out_f.write_bytes(b"partial")
    ok = ffmpeg.flac_to_wav(str(in_f), str(out_f))
    assert ok is False
    # partial should be removed
    assert not out_f.exists()
