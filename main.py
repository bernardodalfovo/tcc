import pandas as pd
import sys
import re

import numpy as np
from matplotlib import pyplot as plt

from classroom_header import Classroom
from student_header import Student

def initialize_student_dict(student_dict: dict):
    """Initialize students' dictionary.

    :return: dictionary with students' names as keys
    """
    student_dict = {}

    for name in report_doc["Nome"]:
        student_dict[name] = Student(name=name)
    
    return student_dict

def find_attendence_columns():
    """Find attendence columns in spreadsheet.
    
    :return: list of strings representing attendence columns
    """
    attendence_columns = []
    for column in report_doc.columns:
        if bool(re.search(r"\d{1,2}\/\d{1,2}\/\d{4}", column)):
            attendence_columns += [column]

    return attendence_columns

def parse_columns(classroom: Classroom):
    """
    """
    attendence_columns = find_attendence_columns()
    for column in attendence_columns:
        date_string = re.search(r"\d{1,2}\/\d{1,2}\/\d{4}", column).group()
        valid = True
        if (report_doc[column] == list(report_doc[column])[0]).all():
            # considerar "?" invalido?
            valid = False
        for index, report in report_doc[column].items():
            score_report = re.search(r"\((\d+)/(\d+)\)", report)
            if score_report is not None:
                score = score_report.group(1)
                max_score = score_report.group(2)

                classroom.students[index].reports[date_string] = {
                    "max_score": float(max_score),
                    "score": float(score),
                    "valid": valid,
                }

if __name__ == "__main__":
    if len(sys.argv) > 1:
        report_path = sys.argv[1]
    else:
        report_path = input("Report path? (ex.: \"report.ods\") ").replace("\"", "")
            

    report_doc = pd.read_excel(report_path, engine="odf", header=3, index_col=0)

    classroom = Classroom(report_doc=report_doc)
    parse_columns(classroom=classroom)
    for _, student in classroom.students.items():
        student.compute_score()
        student.predicted_score = student.interpolate_score()
        student.percentage = student.predicted_score / student.max_score * 100
    
    classroom.measure_weights()
    for _, student in classroom.students.items():
        for index, datapoint in enumerate(student.interpolated_progression):
            if datapoint < classroom.weights[index]:
                student.interpolated_progression_bool += [False]
            else:
                student.interpolated_progression_bool += [True]
        student.classify_dropout()

        # plt.title(f"{student.name} / Reprovado: {student.drop_out}")
        # plt.plot(range(len(student.interpolated_progression)), student.interpolated_progression, "ro")
        # plt.plot(range(len(classroom.weights)), classroom.weights, "-c", alpha=0.5)
        # plt.show()
