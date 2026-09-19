# Fraud metrics

## Goal

Interpret classifier outcomes under severe class imbalance and choose metrics that match the cost of missing a rare event.

## Java mental model

A service-level metric is not automatically a model-quality metric: a single percentage can conceal a harmful failure mode just as an aggregate API latency can hide a slow endpoint.

## Python model

Start with confusion-matrix counts, derive accuracy, precision, recall, and F1, then reason about score-ranking metrics such as ROC-AUC and PR-AUC.

## Key concepts

True and false positives, true and false negatives, accuracy, precision, recall, F1, ROC-AUC, PR-AUC, thresholds, and imbalance.

## Example

`example.py` counts outcomes for a tiny document-classification batch where every confusion-matrix cell is present.

## Exercises

The later fraud-metrics exercises implement formulas and ranking behavior for synthetic payment labels. This document example intentionally does not provide those implementations.

## Self-check

1. What is fraud recall measuring?
2. When can precision fall as recall rises?
3. Why can 99.9% accuracy still be useless?
4. When is PR-AUC more informative than ROC-AUC?
5. Why should a single-class label set reject ranking metrics?

## Done when

You can derive the four confusion counts and explain why accuracy alone is insufficient for rare-event detection.
