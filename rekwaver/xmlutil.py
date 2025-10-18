from xml.etree.ElementTree import parse as xml_parse
from pathlib import Path
from typing import List, Tuple
from .paths import clean_path
from .ffmpeg import get_file_info
from .utils import logger
import shutil


def read_xml(xmlfile: str) -> Tuple[List[str], List[str]]:
    tree = xml_parse(xmlfile)
    root = tree.getroot()
    collection = root.find(".//COLLECTION")
    if collection is None:
        raise ValueError("No COLLECTION element found in XML")

    total_attr = collection.get("Entries")
    if total_attr is None:
        raise ValueError("COLLECTION missing Entries attribute")
    total = int(total_attr)

    tracks = collection.findall(".//TRACK")
    if len(tracks) != total:
        raise ValueError(f"Tracks Length != Entries, {len(tracks)} != {total}")

    wavs = []
    flacs = []
    misc = []

    for track in tracks:
        loc = track.get("Location")
        if not loc:
            continue
        if loc.endswith(".flac"):
            flacs.append(loc)
        elif loc.endswith(".wav"):
            wavs.append(loc)
        else:
            misc.append(loc)

    return wavs, flacs


def ensure_backup(xml_path: str, backup_suffix: str = ".bak") -> str:
    p = Path(xml_path)
    backup = p.with_name(p.name + backup_suffix)
    try:
        if backup.exists():
            logger.info("Backup already exists: %s", backup)
        else:
            shutil.copy2(p, backup)
            logger.info("Created backup: %s", backup)
    except Exception as e:
        logger.error("Failed to create backup %s: %s", backup, e)
    return str(backup)


def replace_flacs_in_xml(
    xml_path: str, replacements: List[Tuple[str, str]], output_path: str | None = None
) -> str:
    ensure_backup(xml_path)
    tree = xml_parse(xml_path)
    root = tree.getroot()

    mapping = dict(replacements)
    changed = 0

    for track in root.findall(".//TRACK"):
        loc = track.get("Location")
        if not loc:
            continue
        if loc in mapping:
            new_loc = mapping[loc]
            track.set("Location", new_loc)
            changed += 1

            try:
                fs_path = clean_path(new_loc)
                info = get_file_info(fs_path)
                fmt = info.get("format", {})
                streams = info.get("streams", [])
                size = fmt.get("size")
                if size:
                    track.set("Size", str(size))
                bitrate = fmt.get("bit_rate")
                if bitrate:
                    track.set("BitRate", str(bitrate))
                if streams:
                    sr = streams[0].get("sample_rate")
                    if sr:
                        track.set("SampleRate", str(sr))
                kind = fmt.get("format_name")
                if not kind and streams:
                    kind = streams[0].get("codec_name")
                if kind:
                    track.set("Kind", str(kind).upper())
            except Exception as e:
                logger.debug("Could not update metadata for %s: %s", new_loc, e)

    if output_path is None:
        p = Path(xml_path)
        output_path = str(p.with_name(p.stem + ".wavified" + p.suffix))

    tree.write(output_path, encoding="utf-8", xml_declaration=True)
    logger.info("Wrote %d replacement(s) to %s", changed, output_path)
    return output_path
