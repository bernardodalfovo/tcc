import pandas as pd
import sys
import re
from datetime import datetime

import numpy as np
from matplotlib import pyplot as plt
from unidecode import unidecode

from classroom_header import Classroom
from student_header import Student

def plot(student: Student):
    """Plot attendances.
    """
    plt.title(f"{student.name}")

    attendance = [i['score'] for _, i in student.attendance_report.items()]
    valids = [i['valid'] for _, i in student.attendance_report.items()]
    mean_score = [i['mean_score'] for _, i in student.attendance_report.items()]

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
            valid_x += [index+1]
        else:
            if interpolated:
                interpolated_datapoints += [student.progression[index]]
            invalid_datapoints += [data]
            invalid_x += [index+1]
            mean_score[index] = student.overall_mean_attendance_score
    
    plt.plot(valid_x, valid_datapoints, 'bo', markersize=10)
    if len(interpolated_datapoints) > 0:
        plt.plot(invalid_x, interpolated_datapoints, 'mo', markersize=10, alpha=0.5)
    else:
        plt.plot(invalid_x, invalid_datapoints, 'ro', markersize=15)
    plt.gca().set_xticks(total_x)
    plt.plot(total_x, mean_score, 'c-', alpha=0.5)
    plt.grid(which='both')
    plt.grid(which='minor', alpha=0.2)
    plt.grid(which='major', alpha=0.5)
    # plt.legend()
    plt.ylabel(ylabel="Pontuação")
    plt.xlim([0,plt.gca().get_xlim()[1]])
    plt.ylim([-0.1,2.1])
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
    """
    """
    attendance_columns = []
    for column in classroom.attendance_report.columns:
        if bool(re.search(r"\d{1,2}\/\d{1,2}\/\d{4}", column)):
            attendance_columns += [column]
    overall_score = []
    for column in attendance_columns:
        class_score = []
        date_string = re.search(r"\d{1,2}\/\d{1,2}\/\d{4}", column).group()
        valid = True
        if (classroom.attendance_report[column] == list(classroom.attendance_report[column])[0]).all():
            # considerar "?" invalido?
            valid = False
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
        for index, report in classroom.attendance_report[column].items():
            score_report = re.search(r"\((\d+)/(\d+)\)", report)
            if score_report is not None:
                classroom.students[index].attendance_report[date_string].update({
                    "mean_score": np.mean(class_score),
                    "missing_rate": round(int(class_score.count(0.0)/len(class_score)*10))/10*100,
                })
    for student in classroom.students.keys():
        classroom.students[student].overall_mean_attendance_score = np.mean(overall_score)

def parse_columns_grades(classroom: Classroom):
    """
    """
    grade_columns = []
    non_grade_column = [
        "total",
        "nome",
        "email",
        "curso",
        "matricula",
        "download",
    ]
    for column in classroom.grade_report.columns:
        is_grade_column = True
        for indicator in non_grade_column:
            if indicator in unidecode(column).lower():
                is_grade_column = False
                break
        if is_grade_column:
            grade_columns += [column]
    for column in grade_columns:
        highest_grade = -1
        all_grades = []
        for i, (_, report) in enumerate(classroom.grade_report[column].items()):
            index = i + 1
            if len(column.split(':')) > 1:
                activity_name = unidecode(' '.join((':'.join(column.split(':')[1:])).split(' ')[:-1])).strip()
            else:
                activity_name = unidecode(' '.join((':'.join(column.split(':')[1])).split(' ')[:-1])).strip()

            try:
                grade = float(report)
            except ValueError:
                grade = -1

            highest_grade = grade if grade > highest_grade else highest_grade
            all_grades += [grade]
            if activity_name not in classroom.students[index].grade_report.keys():
                classroom.students[index].grade_report[activity_name] = {}
            classroom.students[index].grade_report[activity_name].update({
                "grade": grade if grade > -1 else 0,
                "completed": True if grade > -1 else False
            })

        for i, (_, report) in enumerate(classroom.grade_report[column].items()):
            index = i + 1
            classroom.students[index].grade_report[activity_name].update({
                "highest_grade": highest_grade,
                "mean_grade": np.mean([i if i > -1 else 0 for i in all_grades]),
                "completion_rate": len([i for i in all_grades if i > -1]) / len(all_grades),
            })



def parse_columns_activities(classroom: Classroom):
    """
    """
    column_list = list(classroom.activity_report.columns)
    for column_index, column in enumerate(column_list):
        if "email" in column or column in [' ', ''] or 'unnamed' in column.lower():
            continue
        for i, (_, report) in enumerate(classroom.activity_report[column].items()):
            student_index = i + 1
            activity_name = unidecode(column).strip()
            if activity_name not in classroom.students[student_index].activity_report.keys():
                classroom.students[student_index].activity_report[activity_name] = {}
            try:
                completed = unidecode(report).lower() == "concluido"
            except AttributeError:
                continue
            timestamp = (
                            classroom.activity_report.iloc[:, column_index+1][i]
                            if column_index+1 <= len(column_list) and completed
                            else None
                        )
            if timestamp is not None:
                timestamp = datetime.strptime(
                        timestamp,
                        '%A, %d %b %Y, %H:%M'
                    )
            
            classroom.students[student_index].activity_report[activity_name].update({
                "completed": completed,
                "timestamp": timestamp,
            })

if __name__ == "__main__":
    sheet_id = "1WbqYKXmMg4vkyROidhdEsTEaZLPLkySbbTJqSZKTuKQ"
    attendance_sheet_name = "presenca"
    grade_sheet_name = "notas"
    activity_sheet_name = "importantes"

    attendance_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={attendance_sheet_name}"
    grade_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={grade_sheet_name}"
    activity_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={activity_sheet_name}"

            
    attendance_report_doc = pd.read_csv(attendance_url, index_col=0)
    grade_report_doc = pd.read_csv(grade_url, index_col=0)
    activity_report_doc = pd.read_csv(activity_url, index_col=0)

    test_report_doc = pd.read_csv("https://docs.google.com/spreadsheets/d/1mr3nxTdFLpa8i63oHq5l-Fsp0D5h7hu5dVAIOadjvgg/gviz/tq?tqx=out:csv")

    classroom = Classroom(
        attendance_report_doc=attendance_report_doc,
        grade_report_doc=grade_report_doc,
        activity_report_doc=activity_report_doc,
    )

    parse_columns_attendance(classroom=classroom)
    parse_columns_activities(classroom=classroom)
    parse_columns_grades(classroom=classroom)

    # classroom.compute_mean_attendance_score()

    # classroom.measure_weights_attendance()
    # classroom.measure_weights_atividades()
    # classroom.measure_weights_notas()

    #calcular score geral e lugares no ranking
    # calcular risco de desistencia usando quartil

    # true_positive = 0
    # true_negative = 0
    # false_positive = 0
    # false_negative = 0

    scores = []
    
    for _, student in classroom.students.items():
        # student.boolify_progression()
        # for index, datapoint in enumerate(student.chosen_progression):
        #     if (
        #         datapoint < classroom.attendance_weights[index]
        #         or datapoint is None
        #     ):
        #         student.chosen_progression_bool += [False]
        #     else:
        #         student.chosen_progression_bool += [True]

        # student.classify_dropout()

        scores += [student.compute_general_score(interpolate_attendance=False)]

    test_students = [] 
    for index, name in enumerate(test_report_doc["name"]):
        temp_student_ = Student(name=test_report_doc["name"][index], index=-1)
        temp_student_.activity_score = float(test_report_doc["activity_score"][index])
        temp_student_.grade_score = float(test_report_doc["grade_score"][index])
        temp_student_.attendance_score = float(test_report_doc["attendance_score"][index])
        test_students += [temp_student_]

    for student in test_students:
        scores += [student.compute_general_score(interpolate_attendance=False)]

    quartiles = np.quantile(scores, [0, 0.25, 0.5, 0.75, 1])


    safe = []
    relatively_safe = []
    relatively_danger = []
    danger = []


    for _, student in classroom.students.items():
        # plot(student=student)
        if quartiles[3] <= student.general_score <= quartiles[4]:
            safe += [(student, student.general_score)]
        elif quartiles[2] <= student.general_score < quartiles[3]:
            relatively_safe += [(student, student.general_score)]
        elif quartiles[1] <= student.general_score < quartiles[2]:
            relatively_danger += [(student, student.general_score)]
        elif quartiles[0] <= student.general_score < quartiles[1]:
            danger += [(student, student.general_score)]

    for student in test_students:
        # plot(student=student)
        if quartiles[3] <= student.general_score <= quartiles[4]:
            student.classification = "safe"
            safe += [(student, student.general_score)]
        elif quartiles[2] <= student.general_score < quartiles[3]:
            student.classification = "relatively_safe"
            relatively_safe += [(student, student.general_score)]
        elif quartiles[1] <= student.general_score < quartiles[2]:
            student.classification = "relatively_danger"
            relatively_danger += [(student, student.general_score)]
        elif quartiles[0] <= student.general_score < quartiles[1]:
            student.classification = "danger"
            danger += [(student, student.general_score)]
    
    dropout_chart = {
        "safe": safe,
        "relatively_safe": relatively_safe,
        "relatively_danger": relatively_danger,
        "danger": danger,
    }

    results = {
        'name': [],
        'grades_between_0_2_5': [],
        'grades_between_2_5_5': [],
        'grades_between_5_7_5': [],
        'grades_between_7_5_10': [],
        'grades_below_5': [],
        'grades_above_5': [],
        'grades_below_mean': [],
        'grades_above_mean': [],
        'important_activities_complete': [],
        'important_activities_complete_above_average': [],
        'important_activities_complete_below_average': [],
        'important_activities_incomplete': [],
        'important_activities_incomplete_above_average': [],
        'important_activities_incomplete_below_average': [],
        'important_grades_below_mean': [],
        'important_grades_above_mean': [],
        'attendance_above_mean': [],
        'attendance_below_mean': [],
        'missing': [],
        'present': [],
        'partial_presence': [],
        'amount_sequencial_missing': [],
        'missing_0': [],
        'missing_10': [],
        'missing_20': [],
        'missing_30': [],
        'missing_40': [],
        'missing_50': [],
        'missing_60': [],
        'missing_70': [],
        'missing_80': [],
        'missing_90': [],
        'missing_100': [],
        'classification': [],
    }

    result_sheet = pd.DataFrame()

    print()
    for category in dropout_chart.keys():
        print(category)
        print()
        for student in dropout_chart[category]:
            results['name'] += [student[0].name]
            results['grades_between_0_2_5'] += [student[0].grades_between_0_2_5]
            results['grades_between_2_5_5'] += [student[0].grades_between_2_5_5]
            results['grades_between_5_7_5'] += [student[0].grades_between_5_7_5]
            results['grades_between_7_5_10'] += [student[0].grades_between_7_5_10]
            results['grades_below_5'] += [student[0].grades_below_5]
            results['grades_above_5'] += [student[0].grades_above_5]
            results['grades_below_mean'] += [student[0].grades_below_mean]
            results['grades_above_mean'] += [student[0].grades_above_mean]

            results['important_activities_complete'] += [student[0].important_activities_complete]
            results['important_activities_complete_above_average'] += [student[0].important_activities_complete_above_average]
            results['important_activities_complete_below_average'] += [student[0].important_activities_complete_below_average]
            results['important_activities_incomplete'] += [student[0].important_activities_incomplete]
            results['important_activities_incomplete_above_average'] += [student[0].important_activities_incomplete_above_average]
            results['important_activities_incomplete_below_average'] += [student[0].important_activities_incomplete_below_average]
            results['important_grades_below_mean'] += [student[0].important_grades_below_mean]
            results['important_grades_above_mean'] += [student[0].important_grades_above_mean]

            results['attendance_above_mean'] += [student[0].attendance_above_mean]
            results['attendance_below_mean'] += [student[0].attendance_below_mean]
            results['missing'] += [student[0].missing]
            results['present'] += [student[0].present]
            results['partial_presence'] += [student[0].partial_presence]
            results['amount_sequencial_missing'] += [student[0].amount_sequencial_missing]

            for key in student[0].missing_percentage.keys():
                results[f'missing_{int(key)}'] += [student[0].missing_percentage[key]]

            for key in student[0].sequencial_missing.keys():
                attrb_name = f"sequencial_missing_{key}"
                if attrb_name not in results.keys():
                    results[attrb_name] = []
                results[attrb_name] += [student[0].sequencial_missing[key]]

            results['classification'] += [category]


            print(student[0].name, round(student[1], 2))
        print()

    result_sheet = pd.DataFrame(results)

    result_sheet.to_csv('result.csv', index=False)