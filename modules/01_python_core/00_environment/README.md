# Environment and workflow

## Goal

Confirm the interpreter, virtual environment, and test command before writing lessons or exercises.

## Java mental model

Think Maven wrapper plus a selected SDK. Unlike Maven, `uv` manages both Python versions and package environments without a separate build lifecycle.

## Python model

Use `uv sync --all-groups` once, then run tools through `uv run` so every command uses the project environment.

## Key concepts

The interpreter version, isolated environment, and working directory are part of a reproducible result. Keep commands at the repository root and prefer a focused test command while learning.

## Example

Run `uv run python example.py` to print stable interpreter facts.

## Exercises

No coding exercise in this reading lesson; verify your setup before continuing.

## Self-check

1. Which command creates the project environment?
2. Why use `uv run`?
3. Which Python version is the minimum here?
4. Where should commands start?
5. What is a focused test command useful for?

## Done when

`uv run python example.py` and the module example tests run from the repository root.
