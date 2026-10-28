"""Hand-auditable technical sensor slices; no model fitting or fairness verdict."""

from typing import TypedDict


class SliceCounts(TypedDict):
    support: int
    positives: int
    negatives: int
    predicted_positives: int
    tp: int
    fp: int
    fn: int
    tn: int
    selection_rate: float | None
    tpr: float | None
    fpr: float | None
    precision: float | None
    accuracy: float | None


def summarize_rows(
    rows: tuple[tuple[str, int, int], ...], *, groups: tuple[str, ...]
) -> dict[str, SliceCounts]:
    """Summarize (sensor group, reference label, frozen decision) rows."""
    if not groups or any(not isinstance(group, str) or not group.strip() for group in groups):
        raise ValueError("groups must be nonblank strings")
    if len(set(groups)) != len(groups):
        raise ValueError("groups must be unique")
    for group, actual, decision in rows:
        if group not in groups:
            raise ValueError("unknown group")
        if any(type(label) is not int or label not in (0, 1) for label in (actual, decision)):
            raise ValueError("labels must be exact integers zero or one")
    result: dict[str, SliceCounts] = {}
    for group in groups:
        selected = [(actual, decision) for name, actual, decision in rows if name == group]
        tp = sum(actual == 1 and decision == 1 for actual, decision in selected)
        fp = sum(actual == 0 and decision == 1 for actual, decision in selected)
        fn = sum(actual == 1 and decision == 0 for actual, decision in selected)
        tn = sum(actual == 0 and decision == 0 for actual, decision in selected)
        support, positives, negatives, alerts = len(selected), tp + fn, fp + tn, tp + fp
        result[group] = SliceCounts(
            support=support,
            positives=positives,
            negatives=negatives,
            predicted_positives=alerts,
            tp=tp,
            fp=fp,
            fn=fn,
            tn=tn,
            selection_rate=alerts / support if support else None,
            tpr=tp / positives if positives else None,
            fpr=fp / negatives if negatives else None,
            precision=tp / alerts if alerts else None,
            accuracy=(tp + tn) / support if support else None,
        )
    return result


def sampling_demo() -> tuple[dict[str, SliceCounts], dict[str, SliceCounts]]:
    """Change synthetic sampling composition, keeping conditional patterns fixed."""
    a = (("A", 1, 1),) * 3 + (("A", 1, 0), ("A", 0, 1)) + (("A", 0, 0),) * 3
    b = (("B", 1, 1), ("B", 1, 0), ("B", 0, 1), ("B", 0, 0))
    reports = []
    for rows in (a + b, a + b * 3):
        report = summarize_rows(rows, groups=("A", "B"))
        report["all"] = summarize_rows(
            tuple(("all", actual, decision) for _, actual, decision in rows), groups=("all",)
        )["all"]
        reports.append(report)
    return reports[0], reports[1]


def main() -> None:
    """Print the complete table used by bias.md; rounding is display only."""
    print("sample group n TP FP FN TN TPR FPR accuracy")
    for sample, report in zip(("before", "after"), sampling_demo(), strict=True):
        for group, counts in report.items():
            rates = (counts["tpr"], counts["fpr"], counts["accuracy"])
            displayed = " ".join("None" if value is None else f"{value:.3f}" for value in rates)
            print(
                sample,
                group,
                counts["support"],
                counts["tp"],
                counts["fp"],
                counts["fn"],
                counts["tn"],
                displayed,
            )


if __name__ == "__main__":
    main()
