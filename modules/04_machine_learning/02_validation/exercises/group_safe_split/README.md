# Group-safe sensor split

Difficulty: Medium

Estimated time: 45–60 minutes. Prerequisite: validation lesson and Pandas boolean selection.

A park has repeated measurements from several sensors. The next deployment will use
new sensors, so all readings from one sensor must stay in one partition.

Implement `split_sensor_groups` in `starter.py`.

## Contract

1. Require a nonempty frame with a uniquely named `group_column`. Every group value must
   be a nonempty string. Missing values, numeric labels and whitespace-only labels are invalid.
2. Require finite positive train and validation fractions whose sum is below one.
   Let `g` be the number of distinct groups. Use `floor(g * train_fraction)` training
   groups and `floor(g * validation_fraction)` validation groups; the rest go to test.
   Reject a split if any partition would have zero groups.
3. Sort distinct group names lexicographically, then permute them with
   `numpy.random.default_rng(seed).permutation`. Seed is a nonnegative integer.
   Assign the first training count to train, the next validation count to validation,
   and the remainder to test. This rule makes group membership independent of row order.
4. Select all rows belonging to each group set, preserving original row order and indexes.
   Return three independent copies. Do not mutate `frame` or NumPy's global random state.
5. Reject invalid input with `ValueError`. Use a message naming the invalid `group`,
   `column`/`frame`, `fraction`/`partition`, or `seed`; exact wording is otherwise free.

Fractions refer to **groups**. Unequal sensors may produce very different row counts.
This split evaluates new sensors, not future dates; explain that limitation in your notes.

## Edge cases

Interleaved groups, unequal group sizes, duplicate row indexes, fewer groups than rows,
invalid fractions including NaN, missing group IDs, and mutations to returned partitions.

## Run

```powershell
uv run pytest modules/04_machine_learning/02_validation/exercises/group_safe_split -q
```

An untouched boundary is expected-incomplete. Returning overlapping partitions, changing
data or raising an unrelated error fails normally. Done when all assertions pass and
you can explain why a random row split answers a different deployment question.
