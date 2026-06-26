# AI Log

## Environment

- AI assistant: Codex
- Added skill package: `obra/superpowers`
- Relevant workflow skills: `skill-installer`, `using-superpowers`, `brainstorming`, `writing-plans`, `test-driven-development`, `verification-before-completion`

## Interaction 1

Prompt: install `obra/superpowers`.

AI-generated content: installed the Superpowers skills from `https://github.com/obra/superpowers` into the local Codex skills directory.

Manual / edited change: none to project code. Installation was verified by checking that installed skill directories contain `SKILL.md`.

Adoption reason: Superpowers matches the course-required PRD -> design -> test plan -> mock test -> implementation -> verification workflow.

## Interaction 2

Prompt: complete the final project according to the Word PRD.

AI-generated content: extracted PRD requirements, cloned the teacher template, copied public tests, and selected a Level 2 implementation target.

Manual / edited change: personal identity fields such as student ID, name, GitHub username, fork URL, and branch were not invented by AI. They must be filled by the student in the Pull Request template.

Adoption reason: Level 2 covers the required QPSK/AWGN system plus scrambling, plots, mock tests, and design revision records.

## Interaction 3

Prompt: continue implementation.

AI-generated content: wrote tests first, observed the initial import failure, then implemented source codec, scrambler, repetition channel code, framing, QPSK, AWGN, synchronization, pipeline orchestration, CLI, and project documents.

Manual / edited change: the frame design was adjusted after mock analysis to include both original payload length and transmitted channel-coded payload length.

Adoption reason: this avoids hardcoding and makes odd-length payloads, QPSK padding, and channel-coded frames parseable under hidden tests.

## Interaction 4

Prompt: verify against local and public tests.

AI-generated content: ran local tests, the required CLI, and public tests, then fixed issues found by test output.

Manual / edited change: the final AWGN `results/` artifacts are regenerated from the required command before delivery.

Adoption reason: the PRD requires reproducible CLI operation, public-test compatibility, `received.txt`, `metrics.json`, and plots.

## Interaction 5

Prompt: carefully complete all teacher requirements and aim for full score.

AI-generated content: re-audited the PRD, added a Level 3 Rayleigh flat-fading channel with perfect-CSI one-tap equalization, added tests for the extension, rewrote README, added `PRD.md`, and created `REPORT.md`.

Manual / edited change: the required AWGN/QPSK command was preserved. Rayleigh was added as optional `--channel rayleigh` mode.

Adoption reason: this improves the project from public-test completion toward Level 3 scoring while preserving the stable required baseline.

## Interaction 6

Prompt: implement a Web interface for operating the simulation system.

AI-generated content: added `web_app.py`, a local browser UI using Python standard-library `http.server`, plus tests for the home page, `/api/run`, and empty-input validation.

Manual / edited change: the Web UI was designed as a thin wrapper around the existing `run_pipeline()` function rather than a separate simulation implementation.

Adoption reason: this makes the project easier to demonstrate in a defense and adds a GUI-style Level 3 extension without adding dependencies or weakening the teacher's CLI tests.

## Interaction 7

Prompt: enrich the Web interface so it can operate the full communication chain, with source coding, scrambling/encryption, channel coding, framing, QPSK, channel, synchronization, demodulation, decoding, and plots.

AI-generated content: expanded `run_pipeline()` to return a full `stage_trace`, added Web API options for source codec, scrambling mode, and channel coding mode, redesigned the Web page as a complete chain console, and added tests for stage trace plus demo-mode module choices.

Manual / edited change: optional `none` modes were added only for Web demonstration. The required CLI defaults remain PRD-compliant: UTF-8 source coding, PN-XOR scrambling, repetition-3 channel coding, QPSK, and AWGN.

Adoption reason: the richer interface better matches the project goal of explaining every wireless communication module, not just producing a final output file.

## Interaction 8

Prompt: make the Web interface more interactive, with diagrams and paragraphs explaining every step.

AI-generated content: added an interactive lesson panel to the Web UI. Each stage in the communication chain is clickable and displays an SVG schematic, explanatory paragraph, key formula, and live values from the latest simulation run.

Manual / edited change: the diagrams are lightweight inline SVGs and do not require external images or network access.

Adoption reason: the project is easier to present and defend when the interface teaches the communication process instead of only showing final metrics.

## Interaction 9

Prompt: add meaningful score-improving extensions and prepare for defense questions.

AI-generated content: added `scripts/run_experiments.py`, experiment tests, generated SNR/coding/channel comparison outputs, and wrote `DEFENSE_QA.md` with answers to the teacher's likely defense questions.

Manual / edited change: the extension experiments write under `results/experiments/` and do not change the required baseline CLI behavior.

Adoption reason: the added evidence directly supports scoring categories for experiment analysis, code understanding, mock-test revision, and defense explanation.
