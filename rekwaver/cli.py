import argparse
import sys
from .xmlutil import read_xml, replace_flacs_in_xml
from .converter import process_flacs, process_wavs
from .utils import set_verbose, set_log_file


def main():
    parser = argparse.ArgumentParser(description='RekWaver — Convert Wavs & FLACs in a RekordBox Compliant WAV and updates the XML.')
    parser.add_argument('xml', nargs='?', default='./test.xml', help='Path to RekordBox XML (default: ./test.xml)')
    parser.add_argument('-d', '--destination', default=None, help='Destination directory for WAVs')
    parser.add_argument('-p', '--process', choices=['flacs', 'wavs', 'both', 'none'], default='both',
                        help='What to process: flacs, wavs, both, or none')
    parser.add_argument('--dry-run', action='store_true', help="Don't run ffmpeg or create dirs; just show actions")
    parser.add_argument('--update-xml', action='store_true', help='Write an updated XML with WAV locations')
    parser.add_argument('--output-xml', help='Path for updated XML (only used with --update-xml)')
    parser.add_argument('--jobs', type=int, default=1, help='Number of parallel ffmpeg jobs to run (default 1)')
    parser.add_argument('--force', action='store_true', help='Force re-encoding even if target WAV exists')
    parser.add_argument('--log-file', help='Path to write log output (appends).')
    parser.add_argument('-v', '--verbose', action='store_true', help='Enable debug logging')

    args = parser.parse_args()
    set_verbose(args.verbose)
    if args.log_file:
        # default to INFO unless verbose requested
        set_log_file(args.log_file, level='DEBUG' if args.verbose else 'INFO')

    xml_path = args.xml
    try:
        wavs, flacs = read_xml(xml_path)

        updated = []
        dest = args.destination

        if args.process in ('wavs', 'both'):
            process_wavs(wavs, dry_run=args.dry_run)

        if args.process in ('flacs', 'both'):
            updated = process_flacs(flacs, destination=dest, dry_run=args.dry_run, jobs=args.jobs, force=args.force)

        print('Planned/Completed updates:')
        for o, n in updated:
            print(f"{o} -> {n}")

        if args.update_xml:
            if args.dry_run:
                print('Dry run: not writing updated XML (use without --dry-run to apply)')
            else:
                out = replace_flacs_in_xml(xml_path, updated, output_path=args.output_xml)
                print('Wrote updated XML to', out)
    except KeyboardInterrupt:
        print('\nInterrupted by user (Ctrl+C). Exiting...')
        sys.exit(130)
