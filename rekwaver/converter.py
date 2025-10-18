from typing import List
from .paths import clean_path, get_new_path, rekordboxify_path
from .ffmpeg import get_file_info, flac_to_wav
from .utils import logger, DESTINATION
from os.path import exists
from os import makedirs
import concurrent.futures
import os
from pathlib import Path
try:
    from tqdm import tqdm
except Exception:
    tqdm = None


def _is_partial(target: Path, source_path: str) -> tuple[bool, str]:
    """Return (is_partial, reason). Uses ffprobe duration comparison and file size heuristics.

    - If target file is missing or size == 0 -> partial.
    - If both source and target durations are available and differ by >1s -> partial.
    """
    try:
        if not target.exists():
            return True, 'missing'
        size = target.stat().st_size
        if size == 0:
            return True, 'empty_file'

        # try to compare durations
        try:
            src_info = get_file_info(source_path)
            tgt_info = get_file_info(str(target))
            src_dur = float(src_info.get('format', {}).get('duration') or 0)
            tgt_dur = float(tgt_info.get('format', {}).get('duration') or 0)
            if src_dur > 0 and tgt_dur > 0:
                if abs(src_dur - tgt_dur) > 1.0:
                    return True, f'duration_mismatch: src={src_dur:.2f}, tgt={tgt_dur:.2f}'
        except Exception:
            # if ffprobe fails for either file, fall back to size heuristic
            pass

        # heuristic: very small files are likely partial
        if size < 1024 * 10:  # <10KB
            return True, 'very_small'

        return False, ''
    except Exception as e:
        return False, f'check_error: {e}'


def process_wavs(wavs: List[str], dry_run: bool = False):
    for wav in wavs:
        path = clean_path(wav)
        logger.info("Inspecting %s", path)

        try:
            info = get_file_info(path)
        except Exception as e:
            logger.error("Failed to probe %s: %s", path, e)
            continue

        stream = info['streams'][0]

        bits = stream.get('bits_per_raw_sample') or stream.get('bits_per_sample')
        bits_per_sample = int(bits)
        sample_rate = int(stream['sample_rate'])

        if bits_per_sample > 24 or sample_rate > 48000:
            logger.warning("Wav in wrong format: bits_per_sample: %d, sample_rate: %d, loc: %s",
                           bits_per_sample, sample_rate, path)
    logger.info("WAV inspection complete. dry_run=%s", dry_run)


def process_flacs(flacs: List[str], destination: str = DESTINATION, dry_run: bool = False, jobs: int = 1, force: bool = False):
    updated = []
    total = len(flacs)
    processed = 0
    if jobs <= 1 or dry_run:
        # use tqdm progress bar when available so it stays visible in the console
        iterator = flacs
        if tqdm is not None:
            iterator = tqdm(flacs, desc="Converting FLACs", unit="file", leave=True)

        for idx, flac in enumerate(iterator, start=1):
            remaining = total - idx
            path = clean_path(flac)
            try:
                info = get_file_info(path)
            except Exception as e:
                if tqdm is not None:
                    tqdm.write(f"Probe failed: {path}: {e}")
                else:
                    logger.error("Failed to probe %s: %s", path, e)
                continue
            dir_path, new_path = get_new_path(info, destination)
            target = Path(new_path)
            if target.exists() and not force:
                is_partial, reason = _is_partial(target, path)
                if is_partial:
                    if tqdm is not None:
                        tqdm.write(f"Partial target detected ({reason}): {new_path}")
                    else:
                        logger.warning("Partial target detected (%s): %s", reason, new_path)
                    if dry_run:
                        if tqdm is not None:
                            tqdm.write(f"DRY RUN: would remove partial and re-encode {new_path}")
                        else:
                            logger.info("DRY RUN: would remove partial and re-encode %s", new_path)
                        updated.append((flac, rekordboxify_path(new_path)))
                        processed += 1
                        continue
                    try:
                        target.unlink()
                        if tqdm is not None:
                            tqdm.write(f"Removed partial target: {new_path}")
                        else:
                            logger.info("Removed partial target: %s", new_path)
                    except Exception as e:
                        if tqdm is not None:
                            tqdm.write(f"Failed to remove partial target {new_path}: {e}")
                        else:
                            logger.error("Failed to remove partial target %s: %s", new_path, e)
                        # skip this file if we cannot clean it
                        continue
                else:
                    if tqdm is not None:
                        tqdm.write(f"Target exists, skipping conversion: {new_path}")
                    else:
                        logger.info("Target exists, skipping conversion: %s", new_path)
                    updated.append((flac, rekordboxify_path(new_path)))
                    processed += 1
                    continue
            if tqdm is not None:
                tqdm.write(f"[{idx}/{total}] PREP  {Path(path).name} -> {Path(new_path).name} (remaining: {remaining})")
            else:
                logger.info("(%d/%d) Preparing: %s -> %s (remaining: %d)", idx, total, path, new_path, remaining)
            if dry_run:
                if tqdm is not None:
                    tqdm.write(f"DRY RUN: would create dir {dir_path} and convert {path} -> {new_path}")
                else:
                    logger.info("DRY RUN: would create dir %s and convert %s -> %s", dir_path, path, new_path)
                updated.append((flac, rekordboxify_path(new_path)))
                processed += 1
                continue
            if not exists(dir_path):
                makedirs(dir_path, exist_ok=True)
            success = flac_to_wav(path, new_path)
            if success:
                updated.append((flac, rekordboxify_path(new_path)))
                processed += 1
        logger.info("Finished processing FLACs: processed %d/%d, updated %d entries", processed, total, len(updated))
        return updated

    max_workers = jobs if jobs > 0 else (os.cpu_count() or 1)

    def worker(flac_item: str):
        path = clean_path(flac_item)
        try:
            info = get_file_info(path)
        except Exception as e:
            return (flac_item, None, f"probe-failed: {e}")

        try:
            dir_path, new_path = get_new_path(info, destination)
        except Exception as e:
            return (flac_item, None, f"metadata-failed: {e}")

        target = Path(new_path)
        if target.exists() and not force:
            # detect partial; if partial, remove and continue to re-encode
            is_partial, reason = _is_partial(target, path)
            if is_partial:
                logger.warning("Partial target detected (%s): %s", reason, new_path)
                try:
                    target.unlink()
                    logger.info("Removed partial target: %s", new_path)
                except Exception as e:
                    return (flac_item, None, f"rm-failed: {e}")
                # proceed to conversion
            else:
                return (flac_item, rekordboxify_path(new_path), None)

        try:
            if not exists(dir_path):
                makedirs(dir_path, exist_ok=True)
        except Exception as e:
            return (flac_item, None, f"mkdir-failed: {e}")

        ok = flac_to_wav(path, new_path)
        if ok:
            return (flac_item, rekordboxify_path(new_path), None)
        return (flac_item, None, "ffmpeg-failed")

    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as exe:
        futures = {exe.submit(worker, flac): flac for flac in flacs}
        if tqdm is not None:
            pbar = tqdm(total=total, desc="Converting FLACs", unit="file", leave=True, position=0, dynamic_ncols=True)
        else:
            pbar = None
        try:
            for fut in concurrent.futures.as_completed(futures):
                flac_item = futures[fut]
                try:
                    flac_item, new_loc, err = fut.result()
                except Exception as e:
                    # Use tqdm.write if available so message appears above the bar
                    if pbar is not None:
                        tqdm.write(f"Unexpected worker exception for {flac_item}: {e}")
                    else:
                        logger.error("Unexpected worker exception for %s: %s", flac_item, e)
                    new_loc = None
                    err = str(e)
                if new_loc:
                    updated.append((flac_item, new_loc))
                    processed += 1
                    if pbar is not None:
                        tqdm.write(f"Completed {flac_item} -> {new_loc}")
                    else:
                        logger.debug("Completed %s -> %s", flac_item, new_loc)
                else:
                    if pbar is not None:
                        tqdm.write(f"Failed {flac_item}: {err}")
                    else:
                        logger.error("Failed %s: %s", flac_item, err)
                results.append((flac_item, new_loc, err))
                if pbar is not None:
                    pbar.update(1)
        except KeyboardInterrupt:
            logger.info('Interrupted by user, cancelling remaining jobs...')
            for f in futures:
                f.cancel()
            exe.shutdown(wait=False)
            if pbar is not None:
                pbar.close()
            return updated
        finally:
            if pbar is not None:
                pbar.close()
    logger.info("Finished parallel processing FLACs: processed %d/%d, updated %d entries", processed, total, len(updated))
    return updated
