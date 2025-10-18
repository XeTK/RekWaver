from subprocess import run
from json import loads as json_loads
from pathlib import Path
from .utils import logger


def get_file_info(file_path: str):
    cmd = [
        "ffprobe",
        "-v",
        "quiet",
        "-print_format",
        "json",
        "-show_format",
        "-show_streams",
        file_path,
    ]
    result = run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"ffprobe failed for {file_path}: {result.stderr.strip()}")
    info = json_loads(result.stdout)
    return info


def flac_to_wav(input_path, output_path):
    in_path = Path(input_path)
    out_path = Path(output_path)
    try:
        cmd = [
            "ffmpeg",
            "-y",
            "-v",
            "error",
            "-i",
            str(in_path),
            "-ar",
            "48000",
            "-acodec",
            "pcm_s24le",
            str(out_path),
        ]
        result = run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            logger.error(
                "FFmpeg failed for %s\n%s", in_path.name, result.stderr.strip()
            )
            # remove any partially written output file
            try:
                if out_path.exists():
                    out_path.unlink()
                    logger.info("Removed partial output: %s", out_path)
            except Exception as e:
                logger.debug("Failed to remove partial output %s: %s", out_path, e)
            return False
        logger.info("Converted: %s → %s", in_path, out_path)
        return True
    except FileNotFoundError:
        logger.error(
            "FFmpeg not found. Please install it and make sure it's in your PATH."
        )
        return False
    except Exception as e:
        logger.warning("Unexpected error while processing %s: %s", in_path.name, e)
        # cleanup partial output if present
        try:
            if out_path.exists():
                out_path.unlink()
                logger.info("Removed partial output after exception: %s", out_path)
        except Exception as ex:
            logger.debug(
                "Failed to remove partial output %s after exception: %s", out_path, ex
            )
        return False
