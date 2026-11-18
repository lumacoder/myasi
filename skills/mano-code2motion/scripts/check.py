"""Validate MotionSpec and emit a measured sampling report (no external modules)."""
import argparse
import json
import sys
from motion import load, report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('spec')
    args = parser.parse_args()
    try:
        print(json.dumps(report(load(args.spec)), ensure_ascii=False, indent=2))
        return 0
    except (ValueError, OSError) as exc:
        print('invalid: %s' % exc, file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
