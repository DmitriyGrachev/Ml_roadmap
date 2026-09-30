# Environment and workflow

## Goal

Confirm the interpreter, virtual environment, and test command before writing lessons or exercises.

## Java mental model

Think Maven wrapper plus a selected SDK. Unlike Maven, `uv` manages both Python versions and package environments without a separate build lifecycle.

## Python model

Use `uv sync --locked` once, then run tools through `uv run` so every command uses the lightweight project environment. Model libraries are an optional later step in the [training environment guide](../../../docs/compute-guide.md).

## Key concepts

The interpreter version, isolated environment, and working directory are part of a reproducible result. Keep commands at the repository root and prefer a focused test command while learning.

## Example

Run `uv run python modules/01_python_core/00_environment/example.py` to print stable interpreter facts.

## Exercises

Verify the two commands above, then [open the module practice map](../README.md#practice-map) and choose a focused task.

## Self-check

1. Which command creates the project environment?
2. Why use `uv run`?
3. Which Python version is the minimum here?
4. Where should commands start?
5. What is a focused test command useful for?

## Done when

`uv run python modules/01_python_core/00_environment/example.py` and the module example tests run from the repository root.
