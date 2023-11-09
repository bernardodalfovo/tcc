import os
import warnings
from typing import Optional

warnings.filterwarnings("ignore")

import pandas as pd

from Orange.data import Table
from Orange.classification import RandomForestLearner
from Orange.classification import KNNLearner
from Orange.classification import TreeLearner
from Orange.classification import NaiveBayesLearner
from Orange.classification import LogisticRegressionLearner
from Orange.classification import NNClassificationLearner
from Orange.classification import GBClassifier
from Orange.classification import SVMLearner
from Orange.preprocess.score import ANOVA, Chi2, InfoGain, GainRatio
from Orange.preprocess import SelectBestFeatures
from Orange.evaluation import CrossValidation, ShuffleSplit, TestOnTestData

import config
import utils
from classroom_header import Classroom

learners = {
    "random_forest": RandomForestLearner(min_samples_split=5),
    "knn": KNNLearner(),
    "tree": TreeLearner(
        binarize=False, max_depth=None, min_samples_split=1, sufficient_majority=1.0
    ),
    "naive_bayes": NaiveBayesLearner(),
    "logistic_regression": LogisticRegressionLearner(),
    "neural_network": NNClassificationLearner(),
    "gradient_boosting": GBClassifier(),
    "svm": SVMLearner(),
}

feature_selection_methods = {
    "anova": ANOVA(),
    "chi2": Chi2(),
    "info_gain": InfoGain(),
    "gain_ratio": GainRatio(),
    "raw": None,  # no preprocessing
}


evaluation_methods = {
    "xvalidation (k=10)": CrossValidation(k=10, random_state=0, stratified=False),
    "random (n=10, test=20%)": ShuffleSplit(
        n_resamples=10, test_size=0.2, random_state=None, stratified=False
    ),
    f"test_train ({int(config.test_size*100)}/{abs(100 - int(config.test_size*100))})": TestOnTestData(),
}


def repeat_analysis(
    repeat: int,
    classroom: Classroom,
    evaluation_ratio: float,
    res_dict: Optional[dict] = None,
):  # noqa
    if res_dict is None:
        res_dict = {}
    for _ in range(repeat):
        res_dict = implicit_analysis(
            classroom=classroom, evaluation_ratio=evaluation_ratio, res_dict=res_dict
        )
    return res_dict


def implicit_analysis(
    classroom: Classroom, evaluation_ratio: float, res_dict: Optional[dict] = None
):  # noqa
    if res_dict is None:
        res_dict = {}
    classroom.reparse_columns(evaluation_ratio=evaluation_ratio)
    attributes = attribute_extraction(classroom=classroom)
    full_train_filename, train_filename, test_filename = export_attibutes(
        df=attributes,
        dataset=classroom.class_name,
        ratio=evaluation_ratio,
        test_split=config.test_size,
        path="./.temp",
    )
    res_dict = run(
        dataset=classroom.class_name,
        train_location=train_filename,
        ratio_evaluation=evaluation_ratio,
        res_dict=res_dict,
        test_location=test_filename,
        full_train_filename=full_train_filename,
    )
    return res_dict


def export_results(df: pd.DataFrame, filename: str):  # noqa
    df.to_csv(filename, index=False)


def run(
    dataset: str,
    full_train_filename: str,
    ratio_evaluation: float,
    res_dict: dict,
    test_location: Optional[str] = None,
    train_location: Optional[str] = None,
):  # noqa
    full_data = Table.from_file(full_train_filename)
    train_data = Table.from_file(train_location)
    test_data = Table.from_file(test_location) if test_location is not None else None

    if dataset not in res_dict:
        res_dict[dataset] = {}

    if ratio_evaluation not in res_dict[dataset]:
        res_dict[dataset][ratio_evaluation] = {}

    for (
        feature_selection_name,
        feature_selection_method,
    ) in feature_selection_methods.items():
        for n in (
            config.n_best_features if feature_selection_method is not None else [None]
        ):
            if feature_selection_method is not None:
                feature_selection = SelectBestFeatures(
                    method=feature_selection_method, k=n
                )
            else:
                feature_selection = None

            feature_selection_ = (
                f"{feature_selection_name} ({n})"
                if feature_selection is not None
                else feature_selection_name
            )
            if feature_selection_ not in res_dict[dataset][ratio_evaluation]:
                res_dict[dataset][ratio_evaluation][feature_selection_] = {}

            for evaluation_method_name, evaluation_method in evaluation_methods.items():
                if (
                    evaluation_method_name
                    not in res_dict[dataset][ratio_evaluation][feature_selection_]
                ):
                    res_dict[dataset][ratio_evaluation][feature_selection_][
                        evaluation_method_name
                    ] = {}
                for learner_name, learner in learners.items():
                    if (
                        learner_name
                        not in res_dict[dataset][ratio_evaluation][feature_selection_][
                            evaluation_method_name
                        ]
                    ):
                        res_dict[dataset][ratio_evaluation][feature_selection_][
                            evaluation_method_name
                        ][learner_name] = {
                            "TP": 0,
                            "TN": 0,
                            "FP": 0,
                            "FN": 0,
                        }
                    # print(dataset, ratio_evaluation, feature_selection_name, n, evaluation_method_name, learner_name)
                    if "test_train" in evaluation_method_name:
                        if config.test_size > 0.0:
                            evaluation_result = evaluation_method(
                                data=train_data, test_data=test_data, learners=[learner]
                            )
                        else:
                            continue
                    else:
                        evaluation_result = evaluation_method(
                            data=feature_selection(full_data)
                            if feature_selection is not None
                            else full_data,
                            learners=[learner],
                        )
                    # if learner_name == 'tree':
                    #     print(learner(feature_selection(data) if feature_selection is not None else data).print_tree())
                    #     input()

                    actual = evaluation_result.actual
                    predicted = evaluation_result.predicted[0]

                    TP = 0
                    TN = 0
                    FP = 0
                    FN = 0

                    for i in range(len(actual)):
                        if actual[i] == predicted[i]:
                            if actual[i] == 1:
                                TP += 1
                            else:
                                TN += 1
                        else:
                            if actual[i] == 1:
                                FN += 1
                            else:
                                FP += 1

                    res_dict[dataset][ratio_evaluation][feature_selection_][
                        evaluation_method_name
                    ][learner_name]["TP"] += TP
                    res_dict[dataset][ratio_evaluation][feature_selection_][
                        evaluation_method_name
                    ][learner_name]["TN"] += TN
                    res_dict[dataset][ratio_evaluation][feature_selection_][
                        evaluation_method_name
                    ][learner_name]["FP"] += FP
                    res_dict[dataset][ratio_evaluation][feature_selection_][
                        evaluation_method_name
                    ][learner_name]["FN"] += FN

                    # print(res_dict[dataset][ratio_evaluation][feature_selection_][evaluation_method_name][learner_name])

                    for i in range(max(config.n_best_features)):
                        res_dict[dataset][ratio_evaluation][feature_selection_][
                            evaluation_method_name
                        ][learner_name][f"top {i+1}"] = []

                    if feature_selection is not None:
                        top_features = feature_selection(
                            full_data
                            if "test_train" not in evaluation_method_name
                            else train_data
                        ).domain.attributes
                        for i in range(max(config.n_best_features)):
                            if i < len(top_features):
                                res_dict[dataset][ratio_evaluation][feature_selection_][
                                    evaluation_method_name
                                ][learner_name][f"top {i+1}"] += [top_features[i].name]
                            else:
                                res_dict[dataset][ratio_evaluation][feature_selection_][
                                    evaluation_method_name
                                ][learner_name][f"top {i+1}"] += [None]
                    else:
                        for i in range(max(config.n_best_features)):
                            res_dict[dataset][ratio_evaluation][feature_selection_][
                                evaluation_method_name
                            ][learner_name][f"top {i+1}"] += [None]
    # print(res_dict)
    return res_dict


def attribute_extraction(classroom: Classroom) -> dict:  # noqa
    # initialize results dict with flags from Orange
    # s for string
    # c for continuous
    # m for meta
    # d for discrete
    # 'class' for class variable (target)
    results = {
        "name": ["s", "meta"],
        "classification": ["d", "class"],
        "grades_average": ["c", ""],
        "grades_between_0_2_5": ["c", ""],
        "grades_between_2_5_5": ["c", ""],
        "grades_between_5_7_5": ["c", ""],
        "grades_between_7_5_10": ["c", ""],
        "grades_below_5": ["c", ""],
        "grades_below_mean": ["c", ""],
        "important_activities_complete_below_average": ["c", ""],
        "important_activities_incomplete": ["c", ""],
        "important_activities_incomplete_below_average": ["c", ""],
        "important_grades_below_mean": ["c", ""],
        "activities_complete_below_average": ["c", ""],
        "activities_incomplete": ["c", ""],
        "activities_incomplete_below_average": ["c", ""],
        "attendance_below_mean": ["c", ""],
        "missing": ["c", ""],
        "partial_presence": ["c", ""],
        "amount_sequencial_missing": ["c", ""],
    }

    # add sequencial missing attributes
    for i in range(0, 501):
        results[f"sequencial_missing_{i}"] = ["c", ""]

    # attributes are relative to the total of the course/class
    for student in classroom.students.values():
        student.compute_attributes()
        results["name"] += [student.name]
        if student.name in config.hard_to_detect:
            results["classification"] += (
                ["relative"] if config.relative_class else ["positive"]
            )
        elif student.name in config.dropouts:
            results["classification"] += ["positive"]
        else:
            results["classification"] += ["negative"]

        # grades
        total_n_grades = student.grades_below_5 + student.grades_above_5
        results["grades_average"] += [student.grades_sum / total_n_grades]
        results["grades_between_0_2_5"] += [
            student.grades_between_0_2_5 / total_n_grades * 100
        ]
        results["grades_between_2_5_5"] += [
            student.grades_between_2_5_5 / total_n_grades * 100
        ]
        results["grades_between_5_7_5"] += [
            student.grades_between_5_7_5 / total_n_grades * 100
        ]
        results["grades_between_7_5_10"] += [
            student.grades_between_7_5_10 / total_n_grades * 100
        ]
        results["grades_below_5"] += [student.grades_below_5 / total_n_grades * 100]
        results["grades_below_mean"] += [
            student.grades_below_mean / total_n_grades * 100
        ]
        # important activities
        total_n_important = (
            student.important_activities_complete
            + student.important_activities_incomplete
        )
        total_n_important = total_n_important if total_n_important > 0 else 1
        results["important_grades_below_mean"] += [
            student.important_grades_below_mean / total_n_important * 100
        ]
        results["important_activities_incomplete"] += [
            student.important_activities_incomplete / total_n_important * 100
        ]
        results["important_activities_complete_below_average"] += [
            student.important_activities_complete_below_average
            / total_n_important
            * 100
        ]
        results["important_activities_incomplete_below_average"] += [
            student.important_activities_incomplete_below_average
            / total_n_important
            * 100
        ]
        # regular activities
        total_n_activities = student.activities_complete + student.activities_incomplete
        total_n_activities = total_n_activities if total_n_activities > 0 else 1
        results["activities_incomplete"] += [
            student.activities_incomplete / total_n_activities * 100
        ]
        results["activities_complete_below_average"] += [
            student.activities_complete_below_average / total_n_activities * 100
        ]
        results["activities_incomplete_below_average"] += [
            student.activities_incomplete_below_average / total_n_activities * 100
        ]
        # attendance
        total_n_attendance = (
            student.attendance_above_mean + student.attendance_below_mean
        )
        results["attendance_below_mean"] += [
            student.attendance_below_mean / total_n_attendance * 100
        ]
        results["missing"] += [student.missing / total_n_attendance * 100]
        results["partial_presence"] += [
            student.partial_presence / total_n_attendance * 100
        ]
        results["amount_sequencial_missing"] += [student.amount_sequencial_missing]
        for key in student.sequencial_missing.keys():
            attrb_name = f"sequencial_missing_{key}"
            results[attrb_name] += [student.sequencial_missing[key]]

    # if "sequencial_missing_" in key and all elements in list are 0
    # remove key from results after end of loop
    keys_to_remove = []
    for key in results.keys():
        if "sequencial_missing_" in key and all([i == 0 for i in results[key][2:]]):
            keys_to_remove += [key]
    for key in keys_to_remove:
        results.pop(key)

    return pd.DataFrame(results)


def export_attibutes(
    df: pd.DataFrame,
    dataset: str,
    ratio: float,
    test_split: float = 0.2,
    path: str = "./datasets",
):  # noqa
    # df = df.sort_values(by=["name"])
    train_filename = None
    test_filename = None
    if test_split > 0.0:
        train, test = utils.train_test_split(df, test_split)
        train_filename = f"{path}/{dataset}/att_train_{ratio*100}.csv"
        test_filename = f"{path}/{dataset}/att_test_{ratio*100}.csv"
        train.to_csv(train_filename, index=False)
        test.to_csv(test_filename, index=False)
    filename = f"{path}/{dataset}/att_{int(ratio*100)}.csv"
    df.to_csv(filename, index=False)
    return filename, train_filename, test_filename
