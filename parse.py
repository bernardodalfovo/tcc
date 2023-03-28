import pandas as pd
import sys
import re
from scipy.interpolate import interp1d
import numpy as np
from matplotlib import pyplot as plt

if len(sys.argv) > 1:
    report_path = sys.argv[1]
else:
    report_path = input("Report path? (ex.: \"report.ods\") ").replace("\"", "")
        
report_doc = pd.read_excel(report_path, engine="odf", header=3, index_col=0)

class Classroom():
    def __init__(self) -> None:
        self._students = {}
        self.weights = []
        for index, name in report_doc["Nome"].items():
            self._students[index] = Student(name=name, index=index)


class Student():
    def __init__(self, name: str, index: int) -> None:
        self.index = index
        self.name = name
        self.drop_out = False
        self.percentage = 0.0
        self.reports = {}

        self.score = 0.0
        self.max_score = 0.0
        self.predicted_score = 0.0

        self.progression = []
        self.interpolated_progression = []
        self.interpolated_progression_bool = []
    

def initialize_student_dict():
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

                classroom._students[index].reports[date_string] = {
                    "max_score": float(max_score),
                    "score": float(score),
                    "valid": valid,
                }


def compute_score(student: Student):
    """Compute student's attendence score.
    """
    for index, date in enumerate(student.reports.keys()):
        student.max_score += student.reports[date]["max_score"]
        if student.reports[date]["valid"]:
            # remove days in which everyone was present
            student.progression += [(index, student.reports[date]["score"])]

    student.score = np.sum(student.progression)

def interpolate_score(student: Student):
    """
    """
    x = [i[0] for i in student.progression]
    y = [i[1] for i in student.progression]

    f = interp1d(x,y)

    xnew = [i for i in range(len(student.reports.keys())) if i <= x[-1]]
    ynew = f(xnew)

    student.interpolated_progression = ynew
    return sum(ynew)

def classify_dropout(student: Student):
    """
    """
    count_drops = 0
    for datapoint in student.interpolated_progression_bool:
        if not datapoint:
            count_drops += 1
        else:
            count_drops = 0
        if count_drops == 3:
            student.drop_out = True
            break




def measure_weights(classroom: Classroom):
    """Calcula os pesos de cada falta baseado na turma inteira
    """
    weight_array = []
    for index_date in range(len(classroom._students[1].interpolated_progression)):
        weight_date = []
        for index, student in classroom._students.items():
            weight_date += [student.interpolated_progression[index_date]]
        weight_array += [weight_date]
    weight_array = np.array(weight_array)
    weight_array_new = []
    for date in weight_array:
        weight_array_new += [np.mean(date)]
    return np.array(weight_array_new)


classroom = Classroom()
parse_columns(classroom=classroom)
for index, _ in enumerate(classroom._students):
    student = classroom._students[index+1]
    compute_score(student=student)
    student.predicted_score = interpolate_score(student=student)
    student.percentage = student.predicted_score / student.max_score * 100
    # print(student.name, student.predicted_score, student.max_score)
    # if student.percentage >= 75:
    #     print("Enough frequency!")
    # else:
    #     print("FI")

classroom.weights = measure_weights(classroom=classroom)
for _, student in classroom._students.items():
    for index, datapoint in enumerate(student.interpolated_progression):
        if datapoint < classroom.weights[index]:
            student.interpolated_progression_bool += [False]
        else:
            student.interpolated_progression_bool += [True]

    

# for index, _ in enumerate(classroom._students):
#     print(f"{classroom._students[index+1].score / classroom._students[index+1].max_score * 100}")

