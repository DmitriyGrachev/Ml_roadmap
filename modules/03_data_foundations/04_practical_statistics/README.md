# Practical statistics

## Goal

Describe a distribution honestly and distinguish an observed association from a causal explanation.

## Java mental model

Statistics is not a utility-method afterthought: choosing mean, median, variance, or a percentile is a product and monitoring decision, not an interchangeable calculation.

## Python model

Use NumPy aggregations on a well-defined sample, inspect outliers, and communicate what a summary cannot prove.

## Key concepts

Mean, median, population variance, standard deviation, percentiles, distributions, correlation, conditional probability, and Bayesian intuition.

## Example

`example.py` uses median support-response latency so one unusually slow response does not dominate the typical value.

## Exercises

Later exercises use their own payment-alert inputs for a statistical profile and Bayes calculation; this lesson supplies mechanics, not answers.

Продолжение: [парное сравнение потерь моделей](../exercises/paired_model_comparison/README.md) и [рандомизированный A/A–A/B пример](../exercises/randomized_experiment/README.md).

## Self-check

1. Why can median be more robust than mean?
2. What does a percentile communicate?
3. Which variance convention is being used?
4. Why does correlation not prove causation?
5. What information is required for a conditional probability?

## Done when

You can select a descriptive statistic for a monitoring question and state its limitation.
