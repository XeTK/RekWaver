from pathlib import Path
from rekordboxxml.xmlutil import read_xml, replace_flacs_in_xml


SAMPLE_XML = '''<?xml version="1.0" encoding="UTF-8"?>
<DJ_PLAYLISTS>
  <COLLECTION Entries="2">
    <TRACK Location="file://localhost/one.flac" />
    <TRACK Location="file://localhost/two.wav" />
  </COLLECTION>
</DJ_PLAYLISTS>
'''


def test_read_xml(tmp_path):
    p = tmp_path / 'sample.xml'
    p.write_text(SAMPLE_XML)
    wavs, flacs = read_xml(str(p))
    assert len(wavs) == 1
    assert len(flacs) == 1


def test_replace_flacs_in_xml(tmp_path):
    p = tmp_path / 'sample.xml'
    p.write_text(SAMPLE_XML)
    replacements = [('file://localhost/one.flac', 'file://localhost/one.wav')]
    out = replace_flacs_in_xml(str(p), replacements)
    assert Path(out).exists()
    s = Path(out).read_text()
    assert 'one.wav' in s
