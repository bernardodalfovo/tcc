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
    """Plot attendences.
    """
    plt.title(f"{student.name}")

    attendence = [i['score'] for _, i in student.attendence_report.items()]
    valids = [i['valid'] for _, i in student.attendence_report.items()]
    mean_score = [i['mean_score'] for _, i in student.attendence_report.items()]

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

    for index, data in enumerate(attendence):
        if valids[index]:
            valid_datapoints += [data]
            valid_x += [index+1]
        else:
            if interpolated:
                interpolated_datapoints += [student.progression[index]]
            invalid_datapoints += [data]
            invalid_x += [index+1]
            mean_score[index] = student.overall_mean_attendence_score
    
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

    for name in classroom.attendence_report["Nome"]:
        student_dict[name] = Student(name=name)
    
    return student_dict

def parse_columns_attendence(classroom: Classroom):
    """
    """
    attendence_columns = []
    for column in classroom.attendence_report.columns:
        if bool(re.search(r"\d{1,2}\/\d{1,2}\/\d{4}", column)):
            attendence_columns += [column]
    overall_score = []
    for column in attendence_columns:
        class_score = []
        date_string = re.search(r"\d{1,2}\/\d{1,2}\/\d{4}", column).group()
        valid = True
        if (classroom.attendence_report[column] == list(classroom.attendence_report[column])[0]).all():
            # considerar "?" invalido?
            valid = False
        for index, report in classroom.attendence_report[column].items():
            score_report = re.search(r"\((\d+)/(\d+)\)", report)
            if score_report is not None:
                score = score_report.group(1)
                class_score += [float(score)]
                overall_score += [float(score)]
                max_score = score_report.group(2)

                classroom.students[index].attendence_report[date_string] = {
                    "max_score": float(max_score),
                    "score": float(score),
                    "valid": valid,
                }
        for index, report in classroom.attendence_report[column].items():
            score_report = re.search(r"\((\d+)/(\d+)\)", report)
            if score_report is not None:
                classroom.students[index].attendence_report[date_string].update({
                    "mean_score": np.mean(class_score),
                })
    for student in classroom.students.keys():
        classroom.students[student].overall_mean_attendence_score = np.mean(overall_score)

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
                print(column)
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
    attendence_report_path = "./tarefas/presenca.csv"
    grade_report_path = "./tarefas/notas.csv"
    activity_report_path = "./tarefas/importantes.csv"
            
    attendence_report_doc = pd.read_csv(attendence_report_path, header=3, index_col=0, encoding='latin-1', delimiter=';')
    grade_report_doc = pd.read_csv(grade_report_path, header=0, index_col=0, encoding='latin-1', delimiter=';')
    activity_report_doc = pd.read_csv(activity_report_path, header=0, index_col=0, encoding='latin-1', delimiter=';')

    classroom = Classroom(
        attendence_report_doc=attendence_report_doc,
        grade_report_doc=grade_report_doc,
        activity_report_doc=activity_report_doc,
    )

    parse_columns_attendence(classroom=classroom)
    parse_columns_activities(classroom=classroom)
    parse_columns_grades(classroom=classroom)

    # classroom.compute_mean_attendence_score()

    # classroom.measure_weights_attendence()
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
        #         datapoint < classroom.attendence_weights[index]
        #         or datapoint is None
        #     ):
        #         student.chosen_progression_bool += [False]
        #     else:
        #         student.chosen_progression_bool += [True]

        # student.classify_dropout()

        scores += [student.compute_general_score(interpolate_attendence=False)]
    
    quartiles = np.quantile(scores, [0, 0.25, 0.5, 0.75, 1])


    safe = []
    relatively_safe = []
    relatively_danger = []
    danger = []


    for _, student in classroom.students.items():
        # plot(student=student)

        if quartiles[3] <= student.general_score <= quartiles[4]:
            safe += [(student.name, student.general_score)]
        elif quartiles[2] <= student.general_score < quartiles[3]:
            relatively_safe += [(student.name, student.general_score)]
        elif quartiles[1] <= student.general_score < quartiles[2]:
            relatively_danger += [(student.name, student.general_score)]
        elif quartiles[0] <= student.general_score < quartiles[1]:
            danger += [(student.name, student.general_score)]
    
    dropout_chart = {
        "safe": safe,
        "relatively_safe": relatively_safe,
        "relatively_danger": relatively_danger,
        "danger": danger,
    }

    print()
    for category in dropout_chart.keys():
        print(category)
        for student in dropout_chart[category]:
            print(student)
    print()