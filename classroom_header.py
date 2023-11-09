import random
import re
from datetime import datetime

import numpy as np
from unidecode import unidecode

from student_header import Student


class Classroom:  # noqa
    def __init__(
        self,
        attendance_report_doc: any,
        grade_report_doc: any,
        activity_report_doc: any,
        class_name: str,
        evaluation_ratio: float = 1.0,
    ) -> None:  # noqa
        self.class_name = class_name

        self.attendance_report = attendance_report_doc
        self.grade_report = grade_report_doc
        self.activity_report = activity_report_doc

        self.initialize_students()

        self.parse_columns(evaluation_ratio=evaluation_ratio)

    def initialize_students(self):  # noqa
        self.students = {}
        for index, name in self.attendance_report["Nome"].items():
            self.students[index] = Student(name=str(name), index=index)

    def parse_columns(self, evaluation_ratio: float) -> None:  # noqa
        self.parse_columns_attendance(evaluation_ratio=evaluation_ratio)
        self.parse_columns_grades(evaluation_ratio=evaluation_ratio)
        self.parse_columns_activities()

    def reparse_columns(self, evaluation_ratio: float) -> None:  # noqa
        self.initialize_students()
        self.parse_columns(evaluation_ratio=evaluation_ratio)

    def parse_columns_attendance(self, evaluation_ratio: float):
        """Parse columns from attendance report."""
        attendance_columns = []
        for column in self.attendance_report.columns:
            if bool(re.search(r"\d{1,2}\/\d{1,2}\/\d{4}", column)):
                attendance_columns += [column]
        attendance_columns = attendance_columns[
            : int(len(attendance_columns) * evaluation_ratio)
        ]

        max_max_score = 0
        for column in attendance_columns:
            gen_max_score = 0
            for report in list(self.attendance_report[column]):
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
                self.attendance_report[column]
                == list(self.attendance_report[column])[0]
            ).all():
                valid = False

            gen_max_score = 0
            if valid:
                for report in list(self.attendance_report[column]):
                    score_report = re.search(r"\((\d+)/(\d+)\)", str(report))
                    if score_report is not None:
                        gen_max_score = float(score_report.group(2))
                        break

            for index, report in self.attendance_report[column].items():
                score_report = re.search(r"\((\d+)/(\d+)\)", report)
                if score_report is not None:
                    score = score_report.group(1)
                    class_score += [float(score)]
                    overall_score += [float(score)]
                    max_score = score_report.group(2)

                    self.students[index].attendance_report[date_string] = {
                        "max_score": float(max_score),
                        "score": float(score),
                        "valid": valid,
                    }
                elif report == "?" and valid:
                    score = 0.0
                    class_score += [float(score)]
                    overall_score += [float(score)]
                    max_score = gen_max_score

                    self.students[index].attendance_report[date_string] = {
                        "max_score": float(max_score),
                        "score": float(score),
                        "valid": valid,
                    }
                elif report == "?":
                    score = max_max_score
                    class_score += [float(score)]
                    overall_score += [float(score)]
                    max_score = max_max_score

                    self.students[index].attendance_report[date_string] = {
                        "max_score": float(max_score),
                        "score": float(score),
                        "valid": valid,
                    }
            for index, report in self.attendance_report[column].items():
                score_report = re.search(r"\((\d+)/(\d+)\)", report)
                if score_report is not None or report == "?":
                    self.students[index].attendance_report[date_string].update(
                        {
                            "mean_score": np.mean(class_score),
                            "missing_rate": round(
                                int(class_score.count(0.0) / len(class_score) * 10)
                            )
                            / 10
                            * 100,
                        }
                    )
        for student in self.students.keys():
            self.students[student].overall_mean_attendance_score = np.mean(
                overall_score
            )

    def parse_columns_grades(self, evaluation_ratio: float):
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
        for column in self.grade_report.columns:
            is_grade_column = True
            for indicator in non_grade_column:
                if indicator in unidecode(column).lower():
                    is_grade_column = False
                    break
            if is_grade_column:
                grade_columns += [column]

        # randomize columns if ratio_evaluation < 1.0
        # so there is no bias
        if evaluation_ratio < 1.0:
            random.shuffle(grade_columns)
            grade_columns = grade_columns[: int(len(grade_columns) * evaluation_ratio)]

        for column in grade_columns:
            highest_grade = -1
            all_grades = []
            for i, (_, report) in enumerate(self.grade_report[column].items()):
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
                if activity_name not in self.students[index].grade_report.keys():
                    self.students[index].grade_report[activity_name] = {}
                self.students[index].grade_report[activity_name].update(
                    {
                        "grade": grade if grade > -1 else 0,
                        "completed": True if grade > -1 else False,
                        "important": False,
                    }
                )

            for i, (_, report) in enumerate(self.grade_report[column].items()):
                index = i + 1
                self.students[index].grade_report[activity_name].update(
                    {
                        "highest_grade": highest_grade,
                        "mean_grade": np.mean([i if i > -1 else 0 for i in all_grades]),
                        "completion_rate": len([i for i in all_grades if i > -1])
                        / len(all_grades),
                    }
                )

    def parse_columns_activities(self):
        """Parse columns from activity report."""
        column_list = list(self.activity_report.columns)
        for column_index, column in enumerate(column_list):
            if "email" in column or column in [" ", ""] or "unnamed" in column.lower():
                continue
            for i, (_, report) in enumerate(self.activity_report[column].items()):
                student_index = i + 1
                activity_name = unidecode(column).strip()
                if (
                    activity_name
                    not in self.students[student_index].activity_report.keys()
                ):
                    self.students[student_index].activity_report[activity_name] = {}
                try:
                    completed = unidecode(report).lower() == "concluido"
                except AttributeError:
                    continue
                timestamp = (
                    self.activity_report.iloc[:, column_index + 1][i]
                    if column_index + 1 <= len(column_list) and completed
                    else None
                )
                if timestamp is not None:
                    timestamp = datetime.strptime(timestamp, "%A, %d %b %Y, %H:%M")

                self.students[student_index].activity_report[activity_name].update(
                    {
                        "completed": completed,
                        "timestamp": timestamp,
                    }
                )
