import json
import pathlib
import sys


def main() -> int:
    root = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    brief = root / "assets" / "briefs" / "future_courtyard.brief.json"
    data = json.loads(brief.read_text(encoding="utf-8"))
    required = {"schemaVersion", "assetId", "seed", "units", "world", "palette", "character", "budgets"}
    missing = sorted(required.difference(data))
    if missing:
        raise SystemExit(f"missing brief fields: {', '.join(missing)}")
    if data["units"] != "meter":
        raise SystemExit("units must be meter")
    print(f"contract-ok:{data['assetId']} seed={data['seed']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

