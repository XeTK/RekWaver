"""Top-level shim kept for backwards compatibility.

This file is intentionally small — the implementation lives in the
`rekwaver` package. Running this module will call `rekwaver.cli.main()`.
"""

from rekwaver.cli import main


if __name__ == '__main__':
    main()