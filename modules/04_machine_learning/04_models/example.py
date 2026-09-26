"""Small tree-depth search with a reserved plant-classification test set."""

from sklearn.datasets import make_classification
from sklearn.metrics import balanced_accuracy_score
from sklearn.model_selection import GridSearchCV, StratifiedKFold, train_test_split
from sklearn.tree import DecisionTreeClassifier


def select_tree() -> dict[str, float | int]:
    features, labels = make_classification(
        n_samples=120, n_features=4, n_informative=3, n_redundant=0, random_state=21
    )
    train_x, test_x, train_y, test_y = train_test_split(
        features, labels, test_size=0.25, stratify=labels, random_state=21
    )
    search = GridSearchCV(
        DecisionTreeClassifier(min_samples_leaf=3, random_state=21),
        {"max_depth": [1, 2, 3]},
        scoring="balanced_accuracy",
        cv=StratifiedKFold(n_splits=3, shuffle=True, random_state=21),
        n_jobs=1,
        error_score="raise",
    )
    search.fit(train_x, train_y)
    return {
        "selected_depth": int(search.best_params_["max_depth"]),
        "validation_balanced_accuracy": float(search.best_score_),
        "test_balanced_accuracy": float(balanced_accuracy_score(test_y, search.predict(test_x))),
    }


def main() -> None:
    print(select_tree())


if __name__ == "__main__":
    main()
