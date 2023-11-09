def recall(confusion_matrix: dict):  # noqa
    return confusion_matrix["true_positive"] / (
        confusion_matrix["true_positive"] + confusion_matrix["false_negative"]
    )


def precision(confusion_matrix: dict):  # noqa

    return confusion_matrix["true_positive"] / (
        confusion_matrix["true_positive"] + confusion_matrix["false_positive"]
    )


def f1(confusion_matrix: dict):  # noqa
    return (
        2
        * (precision(confusion_matrix) * recall(confusion_matrix))
        / (precision(confusion_matrix) + recall(confusion_matrix))
    )


def accuracy(confusion_matrix: dict):  # noqa
    return (confusion_matrix["true_positive"] + confusion_matrix["true_negative"]) / (
        confusion_matrix["true_positive"]
        + confusion_matrix["true_negative"]
        + confusion_matrix["false_positive"]
        + confusion_matrix["false_negative"]
    )
