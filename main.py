import os

import numpy as np
import pandas as pd

import analise_explicita
import analise_implicita
import config
import metrics
from classroom_header import Classroom


def regular_implicit_analysis(
    classroom: Classroom, sheet_name: str, evaluation_ratio: float
):  # noqa
    res_dict = analise_implicita.repeat_analysis(
        repeat=config.analysis_repeat,
        evaluation_ratio=evaluation_ratio,
        classroom=classroom,
    )
    res_df = {
        "dataset": [],
        "ratio_evaluation": [],
        "evaluation_method": [],
        "feature_selection": [],
        "learner": [],
        "accuracy": [],
        "f1_score": [],
        "precision": [],
        "recall": [],
    }

    # add 'top x' columns
    for i in range(1, max(config.n_best_features) + 1):
        res_df[f"top {i}"] = []

    # turn res_dict to dataframe
    # each key is a separate column
    for dataset in res_dict.keys():
        for ratio_evaluation in res_dict[dataset].keys():
            for feature_selection_ in res_dict[dataset][ratio_evaluation].keys():
                for evaluation_method_name in res_dict[dataset][ratio_evaluation][
                    feature_selection_
                ].keys():
                    for learner_name in res_dict[dataset][ratio_evaluation][
                        feature_selection_
                    ][evaluation_method_name].keys():
                        TP = res_dict[dataset][ratio_evaluation][feature_selection_][
                            evaluation_method_name
                        ][learner_name]["TP"]
                        TN = res_dict[dataset][ratio_evaluation][feature_selection_][
                            evaluation_method_name
                        ][learner_name]["TN"]
                        FP = res_dict[dataset][ratio_evaluation][feature_selection_][
                            evaluation_method_name
                        ][learner_name]["FP"]
                        FN = res_dict[dataset][ratio_evaluation][feature_selection_][
                            evaluation_method_name
                        ][learner_name]["FN"]
                        res_df["dataset"] += [dataset]
                        res_df["ratio_evaluation"] += [ratio_evaluation]
                        res_df["evaluation_method"] += [evaluation_method_name]
                        res_df["feature_selection"] += [feature_selection_]
                        res_df["learner"] += [learner_name]
                        confusion_matrix = {
                            "true_positive": TP,
                            "true_negative": TN,
                            "false_positive": FP,
                            "false_negative": FN,
                        }
                        res_df["accuracy"] += [metrics.accuracy(confusion_matrix)]
                        res_df["f1_score"] += [metrics.f1(confusion_matrix)]
                        res_df["precision"] += [metrics.precision(confusion_matrix)]
                        res_df["recall"] += [metrics.recall(confusion_matrix)]
                        for i in range(
                            len(
                                [
                                    i
                                    for i in res_dict[dataset][ratio_evaluation][
                                        feature_selection_
                                    ][evaluation_method_name][learner_name].keys()
                                    if "top" in i
                                ]
                            )
                        ):
                            res_df[f"top {i+1}"] += res_dict[dataset][ratio_evaluation][
                                feature_selection_
                            ][evaluation_method_name][learner_name][f"top {i+1}"]

    res_df = pd.DataFrame.from_dict(res_df)
    res_df.to_csv(
        "implicit_metrics.csv",
        mode="a",
        header=not os.path.exists("implicit_metrics.csv"),
        index=False,
    )


def three_class_explicit_analysis(
    classroom: Classroom, sheet_name: str, evaluation_ratio: float
):  # noqa
    confusion_matrix = {
        "true_dropout": 0,
        "false_dropout_partial": 0,
        "false_dropout_safe": 0,
        "true_partial": 0,
        "false_partial_dropout": 0,
        "false_partial_safe": 0,
        "false_safe_dropout": 0,
        "false_safe_partial": 0,
        "true_safe": 0,
    }
    # execute explicit analysis with regular weights (1/3 for each)
    confusion_matrix = analise_explicita.repeat_run(
        repeat=config.analysis_repeat,
        evaluation_ratio=evaluation_ratio,
        classroom=classroom,
        grade_w=0.3,
        act_w=0.3,
        att_w=0.4,
        confusion_matrix=confusion_matrix,
    )
    metrics_df = pd.DataFrame.from_dict(
        {
            "sheet_name": [sheet_name],
            "ratio": [evaluation_ratio],
            "TD": [confusion_matrix["true_dropout"]],
            "FDP": [confusion_matrix["false_dropout_partial"]],
            "FDS": [confusion_matrix["false_dropout_safe"]],
            "FPD": [confusion_matrix["false_partial_dropout"]],
            "TP": [confusion_matrix["true_partial"]],
            "FPS": [confusion_matrix["false_partial_safe"]],
            "FSD": [confusion_matrix["false_safe_dropout"]],
            "FSP": [confusion_matrix["false_safe_partial"]],
            "TS": [confusion_matrix["true_safe"]],
        }
    )
    metrics_df.to_csv(
        "3_class_explicit_metrics.csv",
        mode="a",
        header=not os.path.exists("3_class_explicit_metrics.csv"),
        index=False,
    )


def regular_explicit_analysis(
    classroom: Classroom, sheet_name: str, evaluation_ratio: float
):  # noqa
    # execute explicit analysis with regular weights (1/3 for each)
    confusion_matrix = analise_explicita.repeat_run(
        repeat=config.analysis_repeat,
        evaluation_ratio=evaluation_ratio,
        classroom=classroom,
        grade_w=0.3,
        act_w=0.3,
        att_w=0.4,
    )
    recall = metrics.recall(confusion_matrix=confusion_matrix)
    precision = metrics.precision(confusion_matrix=confusion_matrix)
    f1 = metrics.f1(confusion_matrix=confusion_matrix)
    accuracy = metrics.accuracy(confusion_matrix=confusion_matrix)
    metrics_df = pd.DataFrame.from_dict(
        {
            "sheet_name": [sheet_name],
            "ratio": [evaluation_ratio],
            "recall": [recall],
            "precision": [precision],
            "f1": [f1],
            "accuracy": [accuracy],
            "TP": [confusion_matrix["true_positive"]],
            "FP": [confusion_matrix["false_positive"]],
            "TN": [confusion_matrix["true_negative"]],
            "FN": [confusion_matrix["false_negative"]],
        }
    )
    metrics_df.to_csv(
        "explicit_metrics.csv",
        mode="a",
        header=not os.path.exists("explicit_metrics.csv"),
        index=False,
    )


def perceptron_explicit_weights(
    classroom: Classroom, sheet_name: str, evaluation_ratio: float
):  # noqa
    # TODO: use perceptron to find the best combination of weights
    raise NotImplementedError("Explicit weights by Perceptron not implemented yet.")


def brute_force_explicit_weights(
    classroom: Classroom, sheet_name: str, evaluation_ratio: float
):  # noqa
    # test all possible combinatios of grades, activity and attendance weights
    # with a step of 0.1

    # RESULTS: 1/3 for each is within the best combinations for both classes
    metrics_df = pd.DataFrame(
        columns=[
            "sheet_name",
            "ratio",
            "grade_w",
            "act_w",
            "att_w",
            "recall",
            "precision",
            "f1",
            "accuracy",
        ]
    )
    for grade_w in np.arange(0.0, 1.0, 1 / 100):
        for act_w in np.arange(0.0, 1.0, 1 / 100):
            for att_w in np.arange(0.0, 1.0, 1 / 100):
                if round(grade_w + act_w + att_w, 3) == 1.0:
                    grade_w = round(grade_w, 3)
                    act_w = round(act_w, 3)
                    att_w = round(att_w, 3)
                    print(
                        f"{sheet_name}\t{evaluation_ratio}\t{grade_w}\t{act_w}\t{att_w}"
                    )
                    confusion_matrix = analise_explicita.repeat_run(
                        repeat=config.analysis_repeat,
                        evaluation_ratio=evaluation_ratio,
                        classroom=classroom,
                        grade_w=grade_w,
                        act_w=act_w,
                        att_w=att_w,
                    )
                    # print(confusion_matrix)
                    recall = metrics.recall(confusion_matrix=confusion_matrix)
                    precision = metrics.precision(confusion_matrix=confusion_matrix)
                    f1 = metrics.f1(confusion_matrix=confusion_matrix)
                    accuracy = metrics.accuracy(confusion_matrix=confusion_matrix)
                    # add confusion matrix metrics to a pandas dataframe
                    # as well as which weights were used
                    # dict to dataframe
                    a_dict = {
                        "sheet_name": [sheet_name],
                        "ratio": [evaluation_ratio],
                        "grade_w": [grade_w],
                        "act_w": [act_w],
                        "att_w": [att_w],
                        "recall": [recall],
                        "precision": [precision],
                        "f1": [f1],
                        "accuracy": [accuracy],
                    }
                    current_metrics_df = pd.DataFrame.from_dict(a_dict)

                    metrics_df = pd.concat(
                        [metrics_df, current_metrics_df], ignore_index=True
                    )

    # export the dataframe to a csv file, append
    metrics_df.to_csv(
        "explicit_metrics_weights.csv",
        mode="a",
        header=not os.path.exists("explicit_metrics_weights.csv"),
        index=False,
    )


if __name__ == "__main__":
    # remove existing csv files
    if os.path.exists("implicit_metrics.csv"):
        os.remove("implicit_metrics.csv")
    if os.path.exists("explicit_metrics.csv"):
        os.remove("explicit_metrics.csv")
    for sheet_name, sheet_id in config.sheets.items():
        # TODO: move this to utils
        attendance_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={config.attendance_sheet_name}"
        grade_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={config.grade_sheet_name}"
        activity_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={config.activity_sheet_name}"

        attendance_report_doc = pd.read_csv(attendance_url, index_col=0)

        grade_report_doc = pd.read_csv(grade_url, index_col=0)

        try:
            activity_report_doc = pd.read_csv(activity_url, index_col=0)
        except pd.errors.EmptyDataError:
            activity_report_doc = pd.DataFrame()

        classroom = Classroom(
            attendance_report_doc=attendance_report_doc,
            grade_report_doc=grade_report_doc,
            activity_report_doc=activity_report_doc,
            class_name=sheet_name,
        )

        for evaluation_ratio in config.ratio_evaluation:
            print(f"Running: {classroom.class_name} at {evaluation_ratio*100}%")
            # print("Explicit analysis...")
            # brute_force_explicit_weights(classroom=classroom, sheet_name=sheet_name, evaluation_ratio=evaluation_ratio)
            # three_class_explicit_analysis(
            #     classroom=classroom,
            #     sheet_name=sheet_name,
            #     evaluation_ratio=evaluation_ratio,
            # )
            regular_explicit_analysis(
                classroom=classroom,
                sheet_name=sheet_name,
                evaluation_ratio=evaluation_ratio,
            )
            # print("Explicit analysis... done")
            # print("Implicit analysis...")
            # regular_implicit_analysis(
            #     classroom=classroom,
            #     sheet_name=sheet_name,
            #     evaluation_ratio=evaluation_ratio,
            # )
            # print("Explicit analysis... done")
            # print("Implicit analysis...")
            regular_implicit_analysis(
                classroom=classroom,
                sheet_name=sheet_name,
                evaluation_ratio=evaluation_ratio,
            )
            # print("Implicit analysis... done")
