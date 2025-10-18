from rekwaver.paths import clean_path, rekordboxify_path, get_new_path


def test_clean_path_file_url():
    url = "file://localhost/Users/test%20name/song.flac"
    p = clean_path(url)
    assert p.endswith("/Users/test name/song.flac")


def test_rekordboxify_path():
    p = "/tmp/my file.wav"
    url = rekordboxify_path(p)
    assert url.startswith("file://localhost")
    assert "%20" in url


def test_get_new_path_from_info(tmp_path):
    info = {
        "format": {
            "tags": {
                "ARTIST": "The Artist",
                "TITLE": "Some Title",
                "ALBUM": "The Album",
            }
        }
    }
    dest = str(tmp_path / "out")
    dir_path, filename = get_new_path(info, dest)
    assert "The-Artist" in dir_path or "The Artist" in dir_path
    assert filename.endswith(".wav")
