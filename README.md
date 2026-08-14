<div align="center">

# 🎭 Cover Identity

<img src="https://raw.githubusercontent.com/AnonymoDGH/cover-identity/main/logo.png" alt="Cover Identity" width="180"/>

**Fictional legends that hold together.**

[![Python](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![PyPI](https://img.shields.io/badge/PyPI-cover--identity-orange.svg)](https://pypi.org/project/cover-identity/)
[![Platform](https://img.shields.io/badge/platform-osx%20%7C%20linux%20%7C%20windows-lightgrey.svg)]()

> *"The lie isn't the name. The lie is the life that fits it."*

</div>

---

## What is it?

Generates **internally consistent cover identities** — a fictional name, date
of birth, address, phone, email, occupation and a backstory that all agree
with each other, plus the memory anchors that make a legend survivable under
questioning. Deterministic when seeded: the same seed always gives the same
person. Built on Faker, seasoned with fiction.

## Features

- 🧬 Consistency engine — age matches DOB, email matches name, backstory matches dates
- 🧠 Memory anchors — mother's maiden name, childhood pet, first school, plate
- 📜 Backstory generator — a life with an origin and a suspicious fire
- 🎲 Seeded output — reproducible identities for scenes and series
- 🎓 `memorize` drill — quiz yourself until the legend is skin
- 🌍 Any Faker locale — `es_ES`, `fr_FR`, `ja_JP`, ...

## Install

```bash
pip install cover-identity
```

From source:

```bash
git clone https://github.com/AnonymoDGH/cover-identity
cd cover-identity
pip install -e .
```

## Quickstart

```bash
# A legend, printed plain
coverid new --seed 7
# Anaïs Fournier · 34 · 1992-03-14
# 12 Rue des Lilas, Lyon
# +33 6 12 34 56 78 · anaisfournier@outlook.fr
# freelance translator at Fournier & Cie

# A full dossier, ready for the novel's appendix
coverid new --locale fr_FR --seed 7 --format markdown --out legend.md

# Drill until it's yours
coverid memorize --locale fr_FR --seed 7
#  1. Full name: anaïs fournier
#     ✓
```

## CLI reference

| Command | What it does |
|---|---|
| `coverid new [--locale] [--seed] [--format plain\|json\|markdown] [--out <f>]` | Generate an identity |
| `coverid memorize [--locale] [--seed]` | Quiz yourself on the legend |

## How it works

<img src="https://raw.githubusercontent.com/AnonymoDGH/cover-identity/main/assets/architecture.svg" alt="Architecture" width="820"/>

## Tests

```bash
pip install pytest
pytest
```

## License

[MIT](LICENSE) — fictional people for fictional stories. Any resemblance to
real persons is the point, and also a coincidence.
