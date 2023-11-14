from typing import Optional

import numpy as np

import config
from classroom_header import Classroom


def repeat_run(
    repeat: int,
    evaluation_ratio: float,
    classroom: Classroom,
    grade_w: float = 1 / 3,
    act_w: float = 1 / 3,
    att_w: float = 1 / 3,
    confusion_matrix: Optional[dict] = None,
) -> dict:
    """Repeat run."""
    if confusion_matrix is None:
        confusion_matrix = {
            "true_positive": 0,
            "false_positive": 0,
            "true_negative": 0,
            "false_negative": 0,
        }
    for _ in range(repeat):
        classroom.reparse_columns(evaluation_ratio=evaluation_ratio)
        confusion_matrix = run(
            classroom=classroom,
            grade_w=grade_w,
            act_w=act_w,
            att_w=att_w,
            confusion_matrix=confusion_matrix,
        )
    return confusion_matrix


def run(
    classroom: Classroom,
    grade_w: float = 1 / 3,
    act_w: float = 1 / 3,
    att_w: float = 1 / 3,
    confusion_matrix: Optional[dict] = None,
) -> dict:
    """Run main run."""
    if confusion_matrix is None:
        confusion_matrix = {
            "true_positive": 0,
            "false_positive": 0,
            "true_negative": 0,
            "false_negative": 0,
        }
    scores = []

    for _, student in classroom.students.items():
        scores += [
            student.compute_general_score(
                grade_weight=grade_w,
                activity_weight=act_w,
                attendance_weight=att_w,
                interpolate_attendance=config.interpolate_attendance,
            )
        ]

    dropout_chart = {
        "safe": [],
        "partial_safe": [],
        "partial_dropout": [],
        "dropout": [],
    }

    if classroom.class_name == "turma_1":
        percentiles = np.quantile(scores, [0, 0.25, 1])  # turma 1
    elif classroom.class_name == "turma_2":
        percentiles = np.quantile(scores, [0, 0.37, 1])  # turma 2

    percentiles = np.quantile(scores, [0, 0.25, 0.5, 0.75, 1])
    # percentiles = np.quantile(scores, [0, 1/3, 2/3, 1]) # dropout, partial, safe

    if len(percentiles) == 3:
        for _, student in classroom.students.items():
            if percentiles[0] <= student.general_score <= percentiles[1]:
                dropout_chart["dropout"] += [(student, student.general_score)]
            elif percentiles[1] < student.general_score <= percentiles[2]:
                dropout_chart["safe"] += [(student, student.general_score)]
    elif len(percentiles) == 4:
        dropout_chart = {
            "safe": [],
            "partial": [],
            "dropout": [],
        }
        for _, student in classroom.students.items():
            if percentiles[0] <= student.general_score <= percentiles[1]:
                dropout_chart["dropout"] += [(student, student.general_score)]
            elif percentiles[1] < student.general_score <= percentiles[2]:
                dropout_chart["partial"] += [(student, student.general_score)]
            elif percentiles[2] < student.general_score <= percentiles[3]:
                dropout_chart["safe"] += [(student, student.general_score)]
    elif len(percentiles) == 5:
        for _, student in classroom.students.items():
            if percentiles[3] <= student.general_score <= percentiles[4]:
                dropout_chart["safe"] += [(student, student.general_score)]
            elif percentiles[2] <= student.general_score < percentiles[3]:
                dropout_chart["partial_safe"] += [(student, student.general_score)]
            elif percentiles[1] <= student.general_score < percentiles[2]:
                dropout_chart["partial_dropout"] += [(student, student.general_score)]
            elif percentiles[0] <= student.general_score < percentiles[1]:
                dropout_chart["dropout"] += [(student, student.general_score)]
    else:
        raise NotImplementedError(
            "Dropout chart not implemented for this case. Check the percentiles."
        )

    for category in dropout_chart.keys():
        for student in sorted(
            dropout_chart[category], key=lambda x: x[1], reverse=True
        ):
            if len(percentiles) == 3 or len(percentiles) == 5:
                if "dropout" in category:
                    if str(student[0].name) in config.dropouts:
                        confusion_matrix["true_positive"] += 1
                    else:
                        confusion_matrix["false_positive"] += 1
                else:
                    if str(student[0].name) in config.dropouts:
                        confusion_matrix["false_negative"] += 1
                    else:
                        confusion_matrix["true_negative"] += 1
            elif len(percentiles) == 4:
                # make confusion matrix with 3 classes: dropout, partial and safe
                if "dropout" == category:
                    if (
                        str(student[0].name) in config.dropouts
                        and str(student[0].name) not in config.hard_to_detect
                    ):
                        confusion_matrix["true_dropout"] += 1
                    elif str(student[0].name) in config.hard_to_detect:
                        confusion_matrix["false_dropout_partial"] += 1
                    else:
                        confusion_matrix["false_dropout_safe"] += 1
                elif "partial" == category:
                    if str(student[0].name) in config.hard_to_detect:
                        confusion_matrix["true_partial"] += 1
                    elif str(student[0].name) in config.dropouts:
                        confusion_matrix["false_partial_dropout"] += 1
                    else:
                        confusion_matrix["false_partial_safe"] += 1
                elif "safe" == category:
                    if (
                        str(student[0].name) in config.dropouts
                        and str(student[0].name) not in config.hard_to_detect
                    ):
                        confusion_matrix["false_safe_dropout"] += 1
                    elif str(student[0].name) in config.hard_to_detect:
                        confusion_matrix["false_safe_partial"] += 1
                    else:
                        confusion_matrix["true_safe"] += 1
            else:
                raise NotImplementedError(
                    "Dropout chart not implemented for this case. Check the number of categories."
                )

    return confusion_matrix
