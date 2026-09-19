# Splits and leakage

## Goal

Create train, validation, and test partitions that reflect when information would actually be available.

## Java mental model

A temporal split is not a shuffled test fixture: chronological ordering is part of the system contract, much like preserving event order in an event-processing service.

## Python model

Parse timestamps, sort stably, then partition by position so later records cannot teach an earlier prediction task about the future.

## Key concepts

Train, validation, test, leakage, overfitting, underfitting, class imbalance, stable sorting, and temporal boundaries.

## Example

`example.py` orders incoming support documents by receipt time before creating three sequential partitions.

## Exercises

The later time-split exercise specifies its own fractions and transaction schema. This document example only demonstrates the ordering principle.

## Self-check

1. What is data leakage?
2. Why should a temporal split sort first?
3. What role does validation data play?
4. Why can random splitting be inappropriate for events?
5. What does stable sorting protect when timestamps tie?

## Done when

You can demonstrate that every record in training is no later than validation and test records.
