import re
import sys

import numpy as np
import pandas as pd
from matplotlib import pyplot as plt
from scipy.interpolate import interp1d

# if len(sys.argv) > 1:
#     report_path = sys.argv[1]
# else:
#     report_path = input("Report path? (ex.: \"report.ods\") ").replace("\"", "")

# report_doc = pd.read_excel(report_path, engine="odf", header=3, index_col=0)
interpolate = True
classify_dropout_number = 5

# attendance_url = f"https://docs.google.com/spreadsheets/d/1Ol0xuLtDwJw4CndlL__dwKI0cDY3aCvA-ELrBotKn3E/gviz/tq?tqx=out:csv&sheet=presenca" # turma 1
attendance_url = f"https://docs.google.com/spreadsheets/d/1SAY_0d6xP_SffE5kvjmzYPPDRjAm1iLjmXsZ1n6Uzvo/gviz/tq?tqx=out:csv&sheet=presenca"  # turma 2
report_doc = pd.read_csv(attendance_url, index_col=0)

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


class Classroom:  # noqa
    def __init__(self) -> None:  # noqa
        self._students = {}
        self.weights = []
        self.interpolate_weights = []
        for index, name in report_doc["Nome"].items():
            self._students[index] = Student(name=name, index=index)


class Student:  # noqa
    def __init__(self, name: str, index: int) -> None:  # noqa
        self.index = index
        self.name = name
        self.drop_out = False
        # self.drop_out_truth = float(report_doc["Porcentagem"][index].replace(",", ".")) < 75
        self.drop_out_truth = str(name) in dropouts
        self.percentage = 0.0
        self.reports = {}

        self.score = 0.0
        self.max_score = 0.0
        self.predicted_score = 0.0

        self.progression = []
        self.total_progression = []
        self.no_progression = []
        self.interpolated_progression = []
        self.interpolated_progression_bool = []


def initialize_student_dict():
    """Initialize students' dictionary.

    :return: dictionary with students' names as keys
    """
    student_dict = {}

    for index, name in enumerate(report_doc["Nome"]):
        student_dict[name] = Student(name=name)
        # student_dict[name].drop_out_truth = float(report_doc["Porcentagem"][index].replace(",", ".")) < 75

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


def parse_columns(classroom: Classroom):  # noqa
    """"""
    attendence_columns = find_attendence_columns()
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
                }
            elif report == "?" and valid:
                classroom._students[index].reports[date_string] = {
                    "max_score": float(gen_max_score),
                    "score": float(0),
                    "valid": valid,
                }


def compute_score(student: Student):
    """Compute student's attendence score."""
    for index, date in enumerate(student.reports.keys()):
        student.max_score += student.reports[date]["max_score"]
        student.total_progression += [(index, student.reports[date]["score"])]
        if student.reports[date]["valid"] or index == 0:
            # remove days in which everyone was present
            student.progression += [(index, student.reports[date]["score"])]
        elif index + 1 == len(student.reports):
            # get last valid datapoint if very last datapoint is not valid
            # so that interpolation goes until last datapoint
            # student.no_progression += [(student.reports[date]["date"], student.reports[date]["score"], index)]
            for i, data in enumerate(student.progression[::-1]):
                if data is not None:
                    student.progression += [(index, student.reports[date]["score"])]
                    break
        else:
            # student.progression += [(student.reports[date]["date"], student.reports[date]["score"], index)]
            student.no_progression += [(index, student.reports[date]["score"])]

    if not interpolate:
        student.progression = student.total_progression

    student.score = np.sum(student.progression)


def interpolate_score(student: Student):  # noqa
    """"""
    x = [i[0] for i in student.progression]
    y = [i[1] for i in student.progression]

    f = interp1d(x, y)

    xnew = [i for i in range(len(student.reports.keys())) if i <= x[-1]]
    ynew = f(xnew)

    student.interpolated_progression = ynew
    return sum(ynew)


def measure_weights(classroom: Classroom, interpolate_weights: bool):
    """Calcula os pesos de cada falta baseado na turma inteira."""
    weight_array = []
    if interpolate_weights:
        progression_to_check = classroom._students[1].interpolated_progression
    else:
        progression_to_check = classroom._students[1].total_progression
    for index_date in range(len(progression_to_check)):
        # for index_date in range(len(n)):
        weight_date = []
        for index, student in classroom._students.items():
            if interpolate_weights:
                weight_date += [student.interpolated_progression[index_date]]
            else:
                weight_date += [student.total_progression[index_date][1]]
        weight_array += [weight_date]
    weight_array = np.array(weight_array)
    weight_array_new = []
    for date in weight_array:
        weight_array_new += [np.mean(date)]
    return np.array(weight_array_new)


classroom = Classroom()
parse_columns(classroom=classroom)
for index, _ in enumerate(classroom._students):
    student = classroom._students[index + 1]
    compute_score(student=student)
    student.predicted_score = interpolate_score(student=student)
    # student.percentage = student.predicted_score / student.max_score * 100

    # print(student.name, student.predicted_score, student.max_score)
    # if student.percentage >= 75:
    #     print("Enough frequency!")
    # else:
    #     print("FI")

classroom.weights = measure_weights(classroom=classroom, interpolate_weights=False)
if interpolate:
    classroom.interpolate_weights = measure_weights(
        classroom=classroom, interpolate_weights=True
    )
# confusion matrix
confustion_matrix = {
    "true_positive": [],
    "true_negative": [],
    "false_positive": [],
    "false_negative": [],
}
for _, student in classroom._students.items():
    drop_out_count = 0
    if interpolate:
        progression_to_analyze = student.interpolated_progression
    else:
        progression_to_analyze = student.progression
    for index, datapoint in enumerate(progression_to_analyze):
        if type(datapoint) == tuple:
            datapoint = datapoint[1]
        if datapoint < (
            classroom.weights[index]
            if not interpolate
            else classroom.interpolate_weights[index]
        ):
            drop_out_count += 1
        else:
            drop_out_count = 0
        if drop_out_count == classify_dropout_number:
            student.drop_out = True
            break
    if student.drop_out and student.drop_out_truth:
        # print(student.name)
        confustion_matrix["true_positive"] += [student.name]
    elif not student.drop_out and not student.drop_out_truth:
        confustion_matrix["true_negative"] += [student.name]
    elif student.drop_out and not student.drop_out_truth:
        confustion_matrix["false_positive"] += [student.name]
    elif not student.drop_out and student.drop_out_truth:
        print(student.name)
        confustion_matrix["false_negative"] += [student.name]
    #

for category in confustion_matrix.keys():
    print(f"{category}: {len(confustion_matrix[category])}")

# for _, student in classroom._students.items():
#     x_not = np.array(range(len(student.total_progression))) + 1
#     x_interp = np.array(range(len(student.interpolated_progression))) + 1
#     if interpolate:
#         x_ = np.array([i[0] for i in student.no_progression])
#         plt.plot(x_+1, [student.interpolated_progression[i] for i in x_], 'mo', markersize=15, label="Pontuação interpolada", alpha=0.5)
#         plt.plot(x_+1, [student.total_progression[i][1] for i in x_], "ro", markersize=10, label="Pontuação originale")
#         plt.plot(x_interp, classroom.interpolate_weights, '-c', markersize=5, label="Média de pontuação da turma interpolada", alpha=0.5)
#     plt.plot(np.array([i[0] for i in student.progression])+1, [i[1] for i in student.progression], "bo", markersize=10, label="Pontuação original")
#     # plt.plot(x_not, classroom.weights, '-c', markersize=5, label="Média de pontuação da turma", alpha=0.5)

#     plt.gca().set_xticks(x_not)

#     plt.grid(which='both')
#     plt.grid(which='minor', alpha=0.2)
#     plt.grid(which='major', alpha=0.5)
#     # plt.legend(loc='upper center', bbox_to_anchor=(0.5, 1.15))
#     # plt.legend()
#     plt.ylabel(ylabel="Pontuação")
#     plt.xlim([0,plt.gca().get_xlim()[1]])
#     plt.xlabel(xlabel="Aula")
#     plt.show()

# for index, datapoint in enumerate(student.interpolated_progression):
#     if datapoint < classroom.weights[index]:
#         student.interpolated_progression_bool += [False]
#     else:
#         student.interpolated_progression_bool += [True]


# # for index, _ in enumerate(classroom._students):
# #     print(f"{classroom._students[index+1].score / classroom._students[index+1].max_score * 100}")
