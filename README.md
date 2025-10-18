# RekWaver — RekordBox FLAC → WAV Converter

A small utility to convert FLAC files referenced in a RekordBox XML to WAV (pcm_s24le @ 48k) using ffmpeg, and optionally update the XML to point at the new WAV files.

Features
- Parse a RekordBox XML and find TRACK Location entries for `.flac` and `.wav` files.
- Convert FLAC → WAV using `ffmpeg` (configurable destination folder).
- Optionally write an updated XML with WAV locations; creates a `.bak` backup of the original XML the first time it runs.
- Dry-run support for previewing actions without executing ffmpeg or creating files.
- Parallel conversion with the `--jobs` flag (uses threads to run multiple ffmpeg subprocesses).
- Optional progress bar using `tqdm` (if installed).

Prerequisites
- Python 3.10+ (you appear to be using Python 3.11 in this workspace).
- ffmpeg and ffprobe on your PATH. On macOS you can install via Homebrew:

```bash
brew install ffmpeg
```

Installation

1. (Optional) Create a virtual environment and activate it:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

2. Install optional Python dependencies:

```bash
pip install -r requirements.txt
```

Quick usage

```bash
# dry-run: show what would be done without invoking ffmpeg or writing output
python3 init.py path/to/your.xml --dry-run --jobs 4

# convert FLACs to WAVs in parallel (4 jobs), and write updated XML
python3 init.py path/to/your.xml --jobs 4 --update-xml

# inspect WAVs only
python3 init.py path/to/your.xml --process wavs

# use a custom destination for WAVs
python3 init.py path/to/your.xml -d /Volumes/KINGSTON/wavs --update-xml

# enable debug logging
python3 init.py path/to/your.xml --verbose
```

Basic examples:

```bash
# dry-run: show what would be done without invoking ffmpeg or writing output
python3 init.py path/to/your.xml --dry-run --jobs 4

# convert FLACs to WAVs in parallel (4 jobs), and write updated XML
python3 init.py path/to/your.xml --jobs 4 --update-xml

# inspect WAVs only
python3 init.py path/to/your.xml --process wavs

# use a custom destination for WAVs
python3 init.py path/to/your.xml -d /Volumes/KINGSTON/wavs --update-xml

# enable debug logging
python3 init.py path/to/your.xml --verbose

# write log output to a file (appends)
python3 init.py path/to/your.xml --log-file /tmp/rekordbox.log --jobs 4

# force re-encoding even when a target WAV already exists
python3 init.py path/to/your.xml --force --jobs 4

# specify the output xml path when using --update-xml
python3 init.py path/to/your.xml --update-xml --output-xml /tmp/updated.wavified.xml
```

CLI flags (high-level)
- --dry-run: don't run ffmpeg or create directories; just preview actions.
- --update-xml: write an updated XML with WAV locations (creates a .bak the first time).
- --output-xml: custom path for the updated XML when using --update-xml.
- --jobs N: run up to N parallel ffmpeg jobs (default 1). Use higher numbers to speed IO-bound conversion but be mindful of CPU/disk.
- --force: force re-encoding of WAVs even if the target file already exists.
- --log-file PATH: append log output to PATH (includes timestamps). Use --verbose to get DEBUG-level logs.
- --verbose: enable debug logging to console and log file.

Notes
- Backups: the script creates a single backup of the input XML on first load named `<original>.bak`. It will not overwrite that backup on subsequent runs.
- Updated XML: when `--update-xml` is used (and not `--dry-run`) the script will write an updated XML next to the original by default with the suffix `.wavified` (for example `tracks.wavified.xml`), unless you pass `--output-xml` to override.
- Matching: XML replacement is exact-string based on the `Location` attribute found in the TRACK entries. If the script doesn't find matches, consider running without `--dry-run` on a small sample, or ask me to normalize matching (I can change the code to match canonical paths).
- Progress bar: if you install `tqdm` the script will show a clean progress bar during conversion.
- Partial-file detection: the tool detects partially written or corrupted target WAVs and will remove them and re-encode the source. The heuristic uses file size and (when available) duration comparisons via `ffprobe`.
- Logging: use `--log-file PATH` to append logs to a file; logs include timestamps. Use `--verbose` to include DEBUG-level messages.

Importing Rekordbox XML:

1. Import the generated XML into Lexicon DJ ([Lexicon DJ](https://www.lexicondj.com/)).
2. From Lexicon DJ, export the configuration in Rekordbox 7 format and load it into Rekordbox.

Troubleshooting
- If ffmpeg isn't found, you'll see an error; ensure `ffmpeg` and `ffprobe` are in your PATH.
- If conversions fail on some files, the script logs per-file errors and continues with the rest.

Development
- The main code is `init.py` in this repository. You can run it directly as shown above.

License
- This project is released under the MIT License. See the `LICENSE` file for details.
