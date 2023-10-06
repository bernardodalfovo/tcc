import random
import re
import sys
from datetime import datetime

import numpy as np
import pandas as pd
from matplotlib import pyplot as plt
from unidecode import unidecode

from classroom_header import Classroom
from student_header import Student
from utils import train_test_split

ratio_evaluation = 1.0

results = {
    "name": [],
    "classification": [],
    "grades_average": [],
    "grades_between_0_2_5": [],
    "grades_between_2_5_5": [],
    "grades_between_5_7_5": [],
    "grades_between_7_5_10": [],
    "grades_below_5": [],
    # "grades_above_5": [],
    "grades_below_mean": [],
    "grades_above_mean": [],
    # "important_activities_complete": [],
    # "important_activities_complete_above_average": [],
    "important_activities_complete_below_average": [],
    "important_activities_incomplete": [],
    # "important_activities_incomplete_above_average": [],
    "important_activities_incomplete_below_average": [],
    "important_grades_below_mean": [],
    # "important_grades_above_mean": [],
    # "activities_complete": [],
    # "activities_complete_above_average": [],
    "activities_complete_below_average": [],
    "activities_incomplete": [],
    # "activities_incomplete_above_average": [],
    "activities_incomplete_below_average": [],
    # "attendance_above_mean": [],
    "attendance_below_mean": [],
    "missing": [],
    # "present": [],
    "partial_presence": [],
    "amount_sequencial_missing": [],
}


def plot(student: Student):
    """Plot attendances."""
    plt.title(f"{student.name}")

    attendance = [i["score"] for _, i in student.attendance_report.items()]
    valids = [i["valid"] for _, i in student.attendance_report.items()]
    mean_score = [i["mean_score"] for _, i in student.attendance_report.items()]

    total_x = np.array(range(len(mean_score))) + 1

    invalid_x = []
    invalid_datapoints = []
    interpolated_datapoints = []

    valid_x = []
    valid_datapoints = []

    if not all(valids) and None not in student.progression:
        interpolated = True
    else:
        interpolated = False

    for index, data in enumerate(attendance):
        if valids[index]:
            valid_datapoints += [data]
            valid_x += [index + 1]
        else:
            if interpolated:
                interpolated_datapoints += [student.progression[index]]
            invalid_datapoints += [data]
            invalid_x += [index + 1]
            mean_score[index] = student.overall_mean_attendance_score

    plt.plot(valid_x, valid_datapoints, "bo", markersize=10)
    if len(interpolated_datapoints) > 0:
        plt.plot(invalid_x, interpolated_datapoints, "mo", markersize=10, alpha=0.5)
    else:
        plt.plot(invalid_x, invalid_datapoints, "ro", markersize=15)
    plt.gca().set_xticks(total_x)
    plt.plot(total_x, mean_score, "c-", alpha=0.5)
    plt.grid(which="both")
    plt.grid(which="minor", alpha=0.2)
    plt.grid(which="major", alpha=0.5)
    # plt.legend()
    plt.ylabel(ylabel="Pontuação")
    plt.xlim([0, plt.gca().get_xlim()[1]])
    plt.ylim([-0.1, 2.1])
    plt.xlabel(xlabel="Aula")
    plt.show()


def initialize_student_dict(student_dict: dict, classroom: Classroom):
    """Initialize students' dictionary.

    :return: dictionary with students' names as keys
    """
    student_dict = {}

    for name in classroom.attendance_report["Nome"]:
        student_dict[name] = Student(name=name)

    return student_dict


def parse_columns_attendance(classroom: Classroom):
    """Parse columns from attendance report."""
    attendance_columns = []
    for column in classroom.attendance_report.columns:
        if bool(re.search(r"\d{1,2}\/\d{1,2}\/\d{4}", column)):
            attendance_columns += [column]
    attendance_columns = attendance_columns[
        : int(len(attendance_columns) * ratio_evaluation)
    ]

    max_max_score = 0
    for column in attendance_columns:
        gen_max_score = 0
        for report in list(classroom.attendance_report[column]):
            if str(report) == "nan" or report is None:
                continue
            score_report = re.search(r"\((\d+)/(\d+)\)", str(report))
            if score_report is not None:
                gen_max_score = float(score_report.group(2))
                break
        if gen_max_score > max_max_score:
            max_max_score = gen_max_score

    overall_score = []
    for column in attendance_columns:
        class_score = []
        date_string = re.search(r"\d{1,2}\/\d{1,2}\/\d{4}", str(column)).group()
        valid = True
        if (
            classroom.attendance_report[column]
            == list(classroom.attendance_report[column])[0]
        ).all():
            valid = False

        gen_max_score = 0
        if valid:
            for report in list(classroom.attendance_report[column]):
                score_report = re.search(r"\((\d+)/(\d+)\)", str(report))
                if score_report is not None:
                    gen_max_score = float(score_report.group(2))
                    break

        for index, report in classroom.attendance_report[column].items():
            score_report = re.search(r"\((\d+)/(\d+)\)", report)
            if score_report is not None:
                score = score_report.group(1)
                class_score += [float(score)]
                overall_score += [float(score)]
                max_score = score_report.group(2)

                classroom.students[index].attendance_report[date_string] = {
                    "max_score": float(max_score),
                    "score": float(score),
                    "valid": valid,
                }
            elif report == "?" and valid:
                score = 0.0
                class_score += [float(score)]
                overall_score += [float(score)]
                max_score = gen_max_score

                classroom.students[index].attendance_report[date_string] = {
                    "max_score": float(max_score),
                    "score": float(score),
                    "valid": valid,
                }
            elif report == "?":
                score = max_max_score
                class_score += [float(score)]
                overall_score += [float(score)]
                max_score = max_max_score

                classroom.students[index].attendance_report[date_string] = {
                    "max_score": float(max_score),
                    "score": float(score),
                    "valid": valid,
                }
        for index, report in classroom.attendance_report[column].items():
            score_report = re.search(r"\((\d+)/(\d+)\)", report)
            if score_report is not None or report == "?":
                classroom.students[index].attendance_report[date_string].update(
                    {
                        "mean_score": np.mean(class_score),
                        "missing_rate": round(
                            int(class_score.count(0.0) / len(class_score) * 10)
                        )
                        / 10
                        * 100,
                    }
                )
    for student in classroom.students.keys():
        classroom.students[student].overall_mean_attendance_score = np.mean(
            overall_score
        )


def parse_columns_grades(classroom: Classroom):
    """Parse columns from grade report."""
    grade_columns = []
    non_grade_column = [
        "total",
        "nome",
        "email",
        "curso",
        "matricula",
        "download",
        "presenca",
    ]
    for column in classroom.grade_report.columns:
        is_grade_column = True
        for indicator in non_grade_column:
            if indicator in unidecode(column).lower():
                is_grade_column = False
                break
        if is_grade_column:
            grade_columns += [column]

    # randomize columns if ratio_evaluation < 1.0
    # so there is no bias
    if ratio_evaluation < 1.0:
        random.shuffle(grade_columns)
        grade_columns = grade_columns[: int(len(grade_columns) * ratio_evaluation)]
        print(grade_columns)

    for column in grade_columns:
        highest_grade = -1
        all_grades = []
        for i, (_, report) in enumerate(classroom.grade_report[column].items()):
            index = i + 1

            activity_name = column
            if ":" in activity_name:
                if len(column.split(":")) > 1:
                    activity_name = unidecode(
                        " ".join((":".join(column.split(":")[1:])).split(" ")[:-1])
                    ).strip()
                else:
                    activity_name = unidecode(
                        " ".join((":".join(column.split(":")[1])).split(" ")[:-1])
                    ).strip()

            try:
                grade = float(report)
            except ValueError:
                grade = -1

            highest_grade = grade if grade > highest_grade else highest_grade
            all_grades += [grade]
            if activity_name not in classroom.students[index].grade_report.keys():
                classroom.students[index].grade_report[activity_name] = {}
            classroom.students[index].grade_report[activity_name].update(
                {
                    "grade": grade if grade > -1 else 0,
                    "completed": True if grade > -1 else False,
                }
            )

        for i, (_, report) in enumerate(classroom.grade_report[column].items()):
            index = i + 1
            classroom.students[index].grade_report[activity_name].update(
                {
                    "highest_grade": highest_grade,
                    "mean_grade": np.mean([i if i > -1 else 0 for i in all_grades]),
                    "completion_rate": len([i for i in all_grades if i > -1])
                    / len(all_grades),
                }
            )


def parse_columns_activities(classroom: Classroom):
    """Parse columns from activity report."""
    column_list = list(classroom.activity_report.columns)
    for column_index, column in enumerate(column_list):
        if "email" in column or column in [" ", ""] or "unnamed" in column.lower():
            continue
        for i, (_, report) in enumerate(classroom.activity_report[column].items()):
            student_index = i + 1
            activity_name = unidecode(column).strip()
            if (
                activity_name
                not in classroom.students[student_index].activity_report.keys()
            ):
                classroom.students[student_index].activity_report[activity_name] = {}
            try:
                completed = unidecode(report).lower() == "concluido"
            except AttributeError:
                continue
            timestamp = (
                classroom.activity_report.iloc[:, column_index + 1][i]
                if column_index + 1 <= len(column_list) and completed
                else None
            )
            if timestamp is not None:
                timestamp = datetime.strptime(timestamp, "%A, %d %b %Y, %H:%M")

            classroom.students[student_index].activity_report[activity_name].update(
                {
                    "completed": completed,
                    "timestamp": timestamp,
                }
            )


if __name__ == "__main__":
    sheets = [
        # "1WbqYKXmMg4vkyROidhdEsTEaZLPLkySbbTJqSZKTuKQ", # fake, grades, attendence and important activities
        "1Ol0xuLtDwJw4CndlL__dwKI0cDY3aCvA-ELrBotKn3E",  # real, only grades and attendence
        "1SAY_0d6xP_SffE5kvjmzYPPDRjAm1iLjmXsZ1n6Uzvo",  # real 2, only grades and attendence
    ]

    hard_to_detect = [
        # turma 1
        "Aluno 8",  # hard
        "Aluno 16",  # hard
        # turma 2
        "8",  # hard
        "21",  # hard
        "35",  # hard
        "38",  # hard
        "72",  # hard
    ]

    dropouts = [
        # turma 1
        "Aluno 1",
        "Aluno 9",
        "Aluno 10",
        "Aluno 11",
        "Aluno 20",
        "Aluno 30",
        "Aluno 35",
        "Aluno 40",
        # turma 2
        "1",
        "6",
        "11",
        "14",
        "18",
        "20",
        "22",
        "24",
        "31",
        "34",
        "39",
        "44",
        "50",
        "52",
        "54",
        "61",
        "65",
        "66",
        "68",
        "73",
        "74",
        "75",
        "76",
        "78",
        "80",
        "85",
        "86",
    ]

    dropouts += hard_to_detect

    scores = []

    negative = []  # non-dropout
    relatively_negative = []
    relatively_positive = []
    positive = []  # dropout

    attendance_sheet_name = "presenca"
    grade_sheet_name = "notas"
    activity_sheet_name = "importantes"

    for sheet_index, sheet_id in enumerate(sheets):
        attendance_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={attendance_sheet_name}"
        grade_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={grade_sheet_name}"
        activity_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={activity_sheet_name}"

        try:
            attendance_report_doc = pd.read_csv(attendance_url, index_col=0)
        except pd.errors.EmptyDataError:
            attendance_report_doc = pd.DataFrame()

        try:
            grade_report_doc = pd.read_csv(grade_url, index_col=0)
        except pd.errors.EmptyDataError:
            grade_report_doc = pd.DataFrame()

        try:
            activity_report_doc = pd.read_csv(activity_url, index_col=0)
        except pd.errors.EmptyDataError:
            activity_report_doc = pd.DataFrame()

        classroom = Classroom(
            attendance_report_doc=attendance_report_doc,
            grade_report_doc=grade_report_doc,
            activity_report_doc=activity_report_doc,
        )

        parse_columns_attendance(classroom=classroom)
        parse_columns_activities(classroom=classroom)
        parse_columns_grades(classroom=classroom)

        for _, student in classroom.students.items():
            scores += [student.compute_general_score(interpolate_attendance=False)]

        # quartiles = np.quantile(scores, [0, 0.25, 1]) # turma 1
        # quartiles = np.quantile(scores, [0, 0.37, 1]) # turma 2
        quartiles = np.quantile(scores, [0, 0.25, 0.5, 0.75, 1])
        # quartiles = np.quantile(scores, [0, 0.5, 1])

        negative_individual = []
        relatively_negative_individual = []
        relatively_positive_individual = []
        positive_individual = []

        # for _, student in classroom.students.items():
        #     if quartiles[0] <= student.general_score <= quartiles[1]:
        #         positive += [(student, student.general_score)]
        #         positive_individual += [(student, student.general_score)]
        #     elif quartiles[1] < student.general_score <= quartiles[2]:
        #         negative += [(student, student.general_score)]
        #         negative_individual += [(student, student.general_score)]

        for _, student in classroom.students.items():
            if quartiles[3] <= student.general_score <= quartiles[4]:
                negative += [(student, student.general_score)]
                negative_individual += [(student, student.general_score)]
            elif quartiles[2] <= student.general_score < quartiles[3]:
                relatively_negative += [(student, student.general_score)]
                relatively_negative_individual += [(student, student.general_score)]
            elif quartiles[1] <= student.general_score < quartiles[2]:
                relatively_positive += [(student, student.general_score)]
                relatively_positive_individual += [(student, student.general_score)]
            elif quartiles[0] <= student.general_score < quartiles[1]:
                positive += [(student, student.general_score)]
                positive_individual += [(student, student.general_score)]

        dropout_chart_individual = {
            "negative": negative_individual,
            "relatively_negative": relatively_negative_individual,
            "relatively_positive": relatively_positive_individual,
            "positive": positive_individual,
        }

        confusion_matrix = {
            "true_positive": 0,
            "true_negative": 0,
            "false_positive": 0,
            "false_negative": 0,
        }

        for category in dropout_chart_individual.keys():
            # print("\n", category, "\n")
            for student in sorted(
                dropout_chart_individual[category], key=lambda x: x[1], reverse=True
            ):
                # print(student[0].name, round(student[1], 2))
                if "positive" in category:
                    if str(student[0].name) in dropouts:
                        confusion_matrix["true_positive"] += 1
                    else:
                        confusion_matrix["false_positive"] += 1
                else:
                    if str(student[0].name) in dropouts:
                        confusion_matrix["false_negative"] += 1
                    else:
                        confusion_matrix["true_negative"] += 1
        # print(confusion_matrix)
        # print(
        #     "Recall:",
        #     confusion_matrix["true_positive"] / (confusion_matrix["true_positive"] + confusion_matrix["false_negative"])
        # )
        # print(
        #     "Precision:",
        #     confusion_matrix["true_positive"] / (confusion_matrix["true_positive"] + confusion_matrix["false_positive"])
        # )
        # print(
        #     "Accuracy:",
        #     (confusion_matrix["true_positive"] + confusion_matrix["true_negative"]) / sum(confusion_matrix.values())
        # )

    dropout_chart = {
        "negative": negative,
        "relatively_negative": relatively_negative,
        "relatively_positive": relatively_positive,
        "positive": positive,
    }
    # export attributes for implicit analysis
    # attributes are relative to the
    # total of the course
    for category in dropout_chart.keys():
        for student in dropout_chart[category]:
            # name
            results["name"] += [str(student[0].name)]
            # results['classification'] += [category] # categorizes by the classificator
            results["classification"] += [
                "positive" if str(student[0].name) in dropouts else "negative"
            ]  # categorizes by truth
            # grades
            total_n_grades = student[0].grades_below_5 + student[0].grades_above_5
            results["grades_average"] += [student[0].grades_sum / total_n_grades]
            results["grades_between_0_2_5"] += [
                student[0].grades_between_0_2_5 / total_n_grades * 100
            ]
            results["grades_between_2_5_5"] += [
                student[0].grades_between_2_5_5 / total_n_grades * 100
            ]
            results["grades_between_5_7_5"] += [
                student[0].grades_between_5_7_5 / total_n_grades * 100
            ]
            results["grades_between_7_5_10"] += [
                student[0].grades_between_7_5_10 / total_n_grades * 100
            ]
            results["grades_below_5"] += [
                student[0].grades_below_5 / total_n_grades * 100
            ]
            # results["grades_above_5"] += [
            #     student[0].grades_above_5 / total_n_grades * 100
            # ]
            results["grades_below_mean"] += [
                student[0].grades_below_mean / total_n_grades * 100
            ]
            results["grades_above_mean"] += [
                student[0].grades_above_mean / total_n_grades * 100
            ]
            # important activities
            total_n_important = (
                student[0].important_activities_complete
                + student[0].important_activities_incomplete
            )
            total_n_important = total_n_important if total_n_important > 0 else 1
            results["important_grades_below_mean"] += [
                student[0].important_grades_below_mean / total_n_important * 100
            ]
            # results["important_grades_above_mean"] += [
            #     student[0].important_grades_above_mean / total_n_important * 100
            # ]
            # results["important_activities_complete"] += [
            #     student[0].important_activities_complete / total_n_important * 100
            # ]
            results["important_activities_incomplete"] += [
                student[0].important_activities_incomplete / total_n_important * 100
            ]
            # results["important_activities_complete_above_average"] += [
            #     student[0].important_activities_complete_above_average
            #     / total_n_important
            #     * 100
            # ]
            results["important_activities_complete_below_average"] += [
                student[0].important_activities_complete_below_average
                / total_n_important
                * 100
            ]
            # results["important_activities_incomplete_above_average"] += [
            #     student[0].important_activities_incomplete_above_average
            #     / total_n_important
            #     * 100
            # ]
            results["important_activities_incomplete_below_average"] += [
                student[0].important_activities_incomplete_below_average
                / total_n_important
                * 100
            ]
            # regular activities
            total_n_activities = (
                student[0].activities_complete + student[0].activities_incomplete
            )
            total_n_activities = total_n_activities if total_n_activities > 0 else 1
            # results["activities_complete"] += [
            #     student[0].activities_complete / total_n_activities * 100
            # ]
            results["activities_incomplete"] += [
                student[0].activities_incomplete / total_n_activities * 100
            ]
            # results["activities_complete_above_average"] += [
            #     student[0].activities_complete_above_average / total_n_activities * 100
            # ]
            results["activities_complete_below_average"] += [
                student[0].activities_complete_below_average / total_n_activities * 100
            ]
            # results["activities_incomplete_above_average"] += [
            #     student[0].activities_incomplete_above_average
            #     / total_n_activities
            #     * 100
            # ]
            results["activities_incomplete_below_average"] += [
                student[0].activities_incomplete_below_average
                / total_n_activities
                * 100
            ]
            # attendance
            total_n_attendance = (
                student[0].attendance_above_mean + student[0].attendance_below_mean
            )
            # results["attendance_above_mean"] += [
            #     student[0].attendance_above_mean / total_n_attendance * 100
            # ]
            results["attendance_below_mean"] += [
                student[0].attendance_below_mean / total_n_attendance * 100
            ]
            results["missing"] += [student[0].missing / total_n_attendance * 100]
            # results["present"] += [student[0].present / total_n_attendance * 100]
            results["partial_presence"] += [
                student[0].partial_presence / total_n_attendance * 100
            ]
            results["amount_sequencial_missing"] += [
                student[0].amount_sequencial_missing
            ]

            for key in student[0].sequencial_missing.keys():
                attrb_name = f"sequencial_missing_{key}"
                if attrb_name not in results.keys():
                    results[attrb_name] = []
                results[attrb_name] += [student[0].sequencial_missing[key]]

    # get length of all keys in results
    # print them: key, length
    keys_to_remove = []
    for key in results.keys():
        # if "sequencial_missing_" in key and all elements in list are 0
        # remove key from results after end of loop
        if "sequencial_missing_" in key and all([i == 0 for i in results[key]]):
            keys_to_remove += [key]
    for key in keys_to_remove:
        results.pop(key)

    # export results
    result_sheet = pd.DataFrame(results)
    # sort dataframe by name
    result_sheet = result_sheet.sort_values(by=["name"])
    # divide into train and test
    train, test = train_test_split(df=result_sheet, test_size=0.2, dropouts=dropouts)
    # export to csv
    train.to_csv("train.csv", index=False)
    test.to_csv("test.csv", index=False)
    # export to csv
    result_sheet.to_csv("result.csv", index=False)
