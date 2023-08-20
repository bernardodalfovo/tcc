import pandas as pd
import sys
import re
from scipy.interpolate import interp1d
import numpy as np
from matplotlib import pyplot as plt
from datetime import datetime

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
        self.drop_out_truth = False
        self.percentage = 0.0
        self.reports = {}

        self.score = 0.0
        self.max_score = 0.0
        self.predicted_score = 0.0

        self.no_progression = []
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
    # max_max_score = 0
    # for column in attendence_columns:
    #     gen_max_score = 0
    #     for report in list(report_doc[column]):
    #         score_report = re.search(r"\((\d+)/(\d+)\)", report)
    #         if score_report is not None:
    #             gen_max_score = float(score_report.group(2))
    #             break
    #     if gen_max_score > max_max_score:
    #         max_max_score = gen_max_score

    for column in attendence_columns:
        date_string = re.search(r"\d{1,2}\/\d{1,2}\/\d{4}", column).group()
        valid = True
        if (report_doc[column] == list(report_doc[column])[0]).all():
            valid = False

        gen_max_score = 0
        if valid:
            for report in list(report_doc[column]):
                score_report = re.search(r"\((\d+)/(\d+)\)", report)
                if score_report is not None:
                    gen_max_score = float(score_report.group(2))
                    break
        
        for index, report in report_doc[column].items():
            score_report = re.search(r"\((\d+)/(\d+)\)", report)
            if score_report is not None:
                score = score_report.group(1)
                max_score = score_report.group(2)
                classroom._students[index].reports[date_string] = {
                    "max_score": float(max_score),
                    "score": float(score),
                    "valid": valid,
                    "date": datetime.strptime(" ".join(column.split(" ")[0:2]), "%d/%m/%Y %H:%M"),
                }
            elif report == "?" and valid:
                classroom._students[index].reports[date_string] = {
                    "max_score": float(gen_max_score),
                    "score": float(0),
                    "valid": valid,
                    "date": datetime.strptime(" ".join(column.split(" ")[0:2]), "%d/%m/%Y %H:%M"),
                }
            # elif report == "?":
            #     classroom._students[index].reports[date_string] = {
            #         "max_score": max_max_score,
            #         "score": max_max_score,
            #         "valid": valid,
            #         "date": datetime.strptime(" ".join(column.split(" ")[0:2]), "%d/%m/%Y %H:%M"),
            #         "not_marked": True,
            #     }


def compute_score(student: Student):
    """Compute student's attendence score.
    """
    for index, date in enumerate(student.reports.keys()):
        student.max_score += student.reports[date]["max_score"]
        if student.reports[date]["valid"]:
            student.progression += [(student.reports[date]["date"], student.reports[date]["score"], index)]
        elif index+1 == len(student.reports):
            # get last valid datapoint if very last datapoint is not valid
            # so that interpolation goes until last datapoint
            # student.no_progression += [(student.reports[date]["date"], student.reports[date]["score"], index)]
            for i, data in enumerate(student.progression[::-1]):
                if data is not None:
                    student.progression += [(student.reports[date]["date"], data[1], index)]
                    break
        else:
            # student.progression += [(student.reports[date]["date"], student.reports[date]["score"], index)]
            student.no_progression += [(student.reports[date]["date"], student.reports[date]["score"], index)]
            # remove days in which everyone was present

    student.score = np.sum([i[1] for i in student.progression])

def interpolate_score(student: Student):
    """
    """
    x = [i[2] for i in student.progression]
    y = [i[1] for i in student.progression]

    # student.progression = y

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
        if count_drops == 5:
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
    classify_dropout(student=student)
    # for index, datapoint in enumerate(student.interpolated_progression):
        # if datapoint < classroom.weights[index]:
        #     student.interpolated_progression_bool += [False]
        # else:
        #     student.interpolated_progression_bool += [True]


true_positive = 0
true_negative = 0
false_positive = 0
false_negative = 0


    

for index, student in enumerate(classroom._students):
    student = classroom._students[index+1]
    # if student.drop_out and student.dropout_truth:
    #     true_positive += 1
    # elif student.drop_out and not student.dropout_truth:
    #     false_positive += 1
    # elif not student.drop_out and student.dropout_truth:
    #     false_negative += 1
    # plt.title(f"{student.name}")
    x_1 = np.array([i[2] for i in student.no_progression])
    x_2 = np.array(range(len(student.interpolated_progression)))
    if len(student.no_progression) > 0:
        plt.plot(x_1+1, [i[1] for i in student.no_progression], 'ro', markersize=15, label="Pontuação inválida")
    x_interpolated = [(x_2[index], i) for index, i in enumerate(student.interpolated_progression) if index in x_1]
    print(x_interpolated)
    plt.plot(np.array([i[0] for i in x_interpolated])+1, [i[1] for i in x_interpolated], 'mo', markersize=10, label="Pontuação interpolada")
    plt.plot(np.array([i[2] for i in student.progression])+1, [i[1] for i in student.progression], "bo", markersize=10, label="Pontuação original")

    plt.gca().set_xticks(np.array(x_2) + 1)

    # plt.plot(range(len(classroom.attendence_weights)), classroom.attendence_weights, "-c", alpha=0.5)
    plt.grid(which='both')
    # Or if you want different settings for the grids:
    plt.grid(which='minor', alpha=0.2)
    plt.grid(which='major', alpha=0.5)
    plt.legend()
    plt.ylabel(ylabel="Pontuação")
    plt.xlim([0,plt.gca().get_xlim()[1]])
    plt.xlabel(xlabel="Aula")
    plt.show()
    # elif not student.drop_out and not student.dropout_truth:
    #     true_negative += 1
    # print(f"{classroom._students[index+1].score / classroom._students[index+1].max_score * 100}")

