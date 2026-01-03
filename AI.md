# AI.md

This repository contains a Python plugin / extractor for yt-dlp.
This file provides **project context and critical constraints**
that AI assistants must follow when working with the codebase.

For strict, machine-oriented rules see: AGENTS.md and .cursor/rules

---

## Project overview

- Language: Python
- Target project: yt-dlp
- Plugin type: extractor / postprocessor / helper module
- Python version: 3.13
- Primary goals:
  - Correct extraction
  - Compatibility with yt-dlp internals
  - Minimal and safe changes

This project must follow yt-dlp conventions and patterns.

---

## yt-dlp integration rules (CRITICAL)

This project integrates with yt-dlp internals.

- Do NOT invent yt-dlp APIs
- Do NOT assume helper functions or utilities exist
- Do NOT change behavior of existing yt-dlp abstractions

Before using any yt-dlp class, method, or helper:
- Locate it in the yt-dlp source code
- Verify its name, signature, and usage pattern

If an API cannot be found:
- Do NOT invent it
- Stop and ask for clarification

---

## Extractor conventions

If this project implements an extractor:

- Follow existing yt-dlp extractor patterns
- Use similar extractors as reference
- Do not deviate from expected extractor lifecycle

Typical extractor structure must be respected:
- `_VALID_URL`
- `_TESTS`
- `_real_extract`

Do not rename or remove required attributes or methods.

---

## Source of truth

When information conflicts, use the following priority order:

1. Actual Python code in this repository
2. yt-dlp source code
3. Inline comments and docstrings
4. docs/*.md
5. README.md
6. AI.md

Lower-priority sources must not override higher-priority ones.

---

## Compatibility and safety

- Do not break backward compatibility unless explicitly requested
- Avoid using new Python features unless confirmed compatible
- Prefer simple, explicit logic over clever solutions

---

## Refactoring boundaries

AI assistants must NOT:
- Rename public functions or classes
- Change extractor behavior
- Modify yt-dlp integration points
- Perform large refactors unless explicitly requested

If a change affects extraction logic:
- Ask for confirmation
- Describe the impact before applying changes

---

## Error handling

- Follow yt-dlp error handling conventions
- Use existing exception patterns
- Do not swallow errors silently
- Prefer informative error messages consistent with yt-dlp style

---

## Code style expectations

- Follow existing code style in the repository
- Avoid unnecessary abstractions
- Keep functions small and focused
- Prefer readability over micro-optimizations

---

## Task clarity

If task requirements are ambiguous or incomplete:
- Stop before writing code
- Ask clarifying questions
- Do not guess extractor behavior or si
