# Contributing

Thank you for helping improve JØ7 VIREO. Contributions should prioritise safety, reproducibility, accessibility and clear evidence over promotional claims.

## Before opening a change

1. Read [docs/SAFETY.md](docs/SAFETY.md).
2. Search existing issues.
3. Keep hardware-specific behaviour behind configuration where possible.
4. Do not commit private datasets, credentials, personal recordings or unlicensed media.
5. Do not claim human-safety performance without a documented test protocol.

## Development setup

```bash
python3 -m venv .venv
.venv/bin/pip install -e . -r requirements-dev.txt
.venv/bin/ruff check src tests
.venv/bin/pytest -q
```

## Pull requests

A pull request should include:

- the problem being solved;
- the platform and hardware used;
- test evidence;
- impact on accessibility and failure modes;
- documentation updates;
- licensing/provenance for new datasets, models or copied code.

## Code style

- Python 3.10-compatible syntax
- type hints for new public functions
- Ruff-clean code
- unit tests for pure logic
- descriptive GPIO and sensor names
- no machine-specific absolute paths

## Safety-critical changes

Changes to battery systems, motor drivers, servo limits, sensor thresholds or hazard prioritisation require explicit risk notes. Software review is not a substitute for qualified electrical, clinical or mobility-safety review.

## Licence

Unless explicitly stated otherwise, contributions are accepted under AGPL-3.0-or-later. Do not submit code that you do not have the right to license under compatible terms.
