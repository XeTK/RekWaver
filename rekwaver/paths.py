from urllib.parse import unquote, quote, urlparse
from pathlib import Path


def clean_path(value: str) -> str:
    parsed = urlparse(value)
    if parsed.scheme in ("file", ""):
        return unquote(parsed.path or value)
    return unquote(value)


def rekordboxify_path(path: str) -> str:
    quoted_path = quote(path, safe="/:")
    return "file://localhost" + quoted_path


def clean_dir_name(value: str) -> str:
    return (
        value.replace("/", "_")
        .replace("|", "_")
        .replace('"', "")
        .replace(" ", "-")
        .replace(",", "")
        .replace("(", "")
        .replace(")", "")
    )


def get_new_path(info, destination: str):
    fmt = info.get("format", {})
    tags = fmt.get("tags", {})
    if not tags:
        raise ValueError(f"No metadata on FLAC File: {fmt.get('filename')}")

    artist = clean_dir_name(tags.get("ARTIST", "Unknown Artist"))
    title = clean_dir_name(tags.get("TITLE", "Unknown Title"))
    album = clean_dir_name(tags.get("ALBUM", ""))

    directory = Path(destination) / artist / album
    filename = str(directory / f"{artist}-{title}.wav")
    return str(directory), filename
