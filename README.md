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

Generates **internally consistent cover identities** — and everything that
keeps one alive. A legend is more than a name and a date of birth: it is a
dated life history, a paper trail, a social web, a digital footprint, a
routine, a budget, a passport, a medical card, a vehicle, a set of duress
codes, and a plan for the day it burns. This package builds all of it,
deterministically, from a single seed — then audits it, scores its risk,
drills the operator on it, and stress-tests it under interrogation.

Built on Faker, seasoned with fiction. For novels, roleplay, and testing.

## Features

**The legend**
- 🧬 Consistency engine — age matches DOB, email matches name, timeline is chronological
- 📅 Timeline generator — a dated life history anchored to the date of birth
- 🎭 Personas — archetype templates (tradesperson, creative, clerk, host, scholar)
- 🗣️ Speech kit — fillers, deflections, safe topics, and legend-leakage scoring
- 🧍 Appearance — baseline description plus a reversible disguise kit

**The supporting material**
- 📄 Paper trail — library card, gym membership, utility bill, work badge, receipts
- 🕸️ Network — a small social web with vouch-worthy contacts
- 🌐 Digital footprint — sparse, boring, on-legend accounts and posts
- 💰 Finance — income, budget, transactions, and a deliberately average credit profile
- ✈️ Travel — passport history scaled to the persona
- 🏠 Residence — home, safe houses, and neighborhood knowledge
- 🚗 Vehicles — a car with a plate, and routes to know cold
- 🏥 Medical — blood type, allergies, and a boring medical story
- 🗓️ Habits — a contiguous daily routine and small lived-in details
- 🌍 Languages — native tongue, accent, and honest proficiency levels

**Operating it**
- 🧠 Memory drill — scored memorization with a 0–100 burn meter
- 🕵️ Interrogation — adversarial probes that pull on the legend's weak threads
- 🎬 Scenarios — rehearsal cards built from the legend's own details
- 🛡️ Tradecraft — dead drops, brush passes, SDR routes, signal sites (fictional)
- 🔥 Burn plan — graded compromise response from lay-low to evacuate
- 📞 Comms — check-in schedule and missed-contact escalation ladder
- ✅ Checklists — pre-meeting, pre-travel, and post-incident walks
- 📋 Readiness — go/no-go gates before a legend goes live
- 🔄 Rotation — legend lifecycle scheduling with expiry horizons
- 🧾 Debrief — post-operation review that names the fields to fix
- 🗂️ Alias graph — cross-contamination checks between active aliases
- 📊 Metrics — generator quality and diversity over a seeded sample
- 🖥️ Handler dashboard — one status board across many legends

**Storage**
- 🔐 Vault — passphrase-protected, tamper-evident encrypted legend storage

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

# The complete dossier — identity, paper trail, network, footprint,
# finances, travel, medical, residence, tradecraft, and more
coverid dossier --seed 7 --today 2024-06-01

# Apply an archetype
coverid persona tradesperson --seed 7

# Audit for contradictions
coverid audit --seed 7 --today 2024-06-01

# Drill until it's yours (study mode prints the answers)
coverid drill --seed 7 --study

# Exposure-risk assessment
coverid risk --seed 7 --today 2024-06-01

# Pre-deployment go/no-go gates
coverid readiness --seed 7 --today 2024-06-01 --drill-meter 90

# Encrypt a legend into a vault, then read it back
coverid vault-save berlin --passphrase "correct horse" --seed 7 --out legends.vault
coverid vault-show legends.vault --passphrase "correct horse"

# Multi-legend status board
coverid dashboard --seeds 1 2 3 --names berlin oslo kyoto --activate berlin
```

## CLI reference

| Command | What it does |
|---|---|
| `coverid new` | Generate an identity |
| `coverid memorize` | Quiz yourself on the legend |
| `coverid dossier` | Assemble the complete dossier (briefing/json/markdown/cheat-sheet/redacted) |
| `coverid persona` | List or apply an archetype |
| `coverid audit` | Check an identity for contradictions |
| `coverid timeline` | Show the dated life history and gaps |
| `coverid drill` | Scored memorization drill with a burn meter |
| `coverid interrogate` | Adversarial probe list |
| `coverid risk` | Exposure-risk assessment |
| `coverid readiness` | Pre-deployment go/no-go gates |
| `coverid wallet` | Fabricate the paper trail |
| `coverid network` | Build the social web |
| `coverid footprint` | Build the digital footprint |
| `coverid tradecraft` | Fictional operations plan |
| `coverid burn` | Compromise response plan |
| `coverid schedule` | Check-in schedule and escalation ladder |
| `coverid checklist` | Pre-action checklists |
| `coverid scenarios` | Rehearsal scenario cards |
| `coverid metrics` | Generator quality metrics |
| `coverid debrief` | Post-operation review (stdin) |
| `coverid dashboard` | Multi-legend status board |
| `coverid vault-save` / `coverid vault-show` | Encrypted legend storage |

## How it works

<img src="https://raw.githubusercontent.com/AnonymoDGH/cover-identity/main/assets/architecture.svg" alt="Architecture" width="820"/>

## Tests

```bash
pip install pytest
pytest
```

423 tests cover every module, the CLI, and the end-to-end lifecycle.

## License

[MIT](LICENSE) — fictional people for fictional stories. Any resemblance to
real persons is the point, and also a coincidence.
