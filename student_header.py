import numpy as np
from scipy.interpolate import interp1d


class Student:
    """Student class."""

    def __init__(self, name: str, index: int) -> None:
        """Initialize student object."""
        self.index = index
        self.name = name
        self.percentage = 0.0

        self.progression = []
        self.weighted_progression = []

        # self.missing_rate = []
        self.mean_scores = []
        self.max_score = []

        self.general_score = None
        self.overall_mean_attendance_score = None
        self.computed_important_activities = False

        self.grade_report = {}
        self.grade_score = None
        self.grades_between_0_2_5 = 0
        self.grades_between_2_5_5 = 0
        self.grades_between_5_7_5 = 0
        self.grades_between_7_5_10 = 0
        self.grades_below_5 = 0
        self.grades_above_5 = 0
        self.grades_below_mean = 0
        self.grades_above_mean = 0
        self.grades_sum = 0

        self.activity_report = {}
        self.activity_score = None
        self.important_activities_complete = 0
        self.important_activities_complete_majority = 0
        self.important_activities_complete_minority = 0
        self.important_activities_incomplete = 0
        self.important_activities_incomplete_majority = 0
        self.important_activities_incomplete_minority = 0
        self.important_grades_below_mean = 0
        self.important_grades_above_mean = 0

        self.activities_complete = 0
        self.activities_complete_majority = 0
        self.activities_complete_minority = 0
        self.activities_incomplete = 0
        self.activities_incomplete_majority = 0
        self.activities_incomplete_minority = 0

        self.attendance_report = {}
        self.attendance_score = None
        self.attendance_above_mean = 0
        self.attendance_below_mean = 0
        self.missing = 0
        self.present = 0
        self.partial_presence = 0
        self.amount_sequencial_missing = 0
        # self.missing_percentage = {
        #     0.0: 0,
        #     10.0: 0,
        #     20.0: 0,
        #     30.0: 0,
        #     40.0: 0,
        #     50.0: 0,
        #     60.0: 0,
        #     70.0: 0,
        #     80.0: 0,
        #     90.0: 0,
        #     100.0: 0,
        # }

        self.sequencial_missing = {}
        for i in range(0, 501):
            self.sequencial_missing[i] = 0

    def compute_general_score(
        self,
        grade_weight: float,
        activity_weight: float,
        attendance_weight: float,
        interpolate_attendance: bool = False,
    ):
        """Calcula a pontuacao geral do aluno no ranking.

        Leva em consideracao presenca (1/3), notas (1/3) e realizacao de atividades
        (1/3).
        """
        self.grade_score = (
            self.compute_grade_score() if self.grade_score is None else self.grade_score
        )
        self.completion_score = (
            self.compute_activity_completion_score()
            if self.activity_score is None
            else self.activity_score
        )
        self.attendance_score = (
            self.compute_attendance_score(interpolate=interpolate_attendance)
            if self.attendance_score is None
            else self.attendance_score
        )

        # print(f"{self.name}, Grade: {round(grade_score, 2)}, Activity completion: {round(completion_score, 2)}, attendance: {round(attendance_score, 2)}")

        self.general_score = (
            self.grade_score * grade_weight
            + self.completion_score * activity_weight
            + self.attendance_score * attendance_weight
        )

        return self.general_score

    def compute_grade_score(self):
        """Calcula o score associado a notas e pesos atribuidos."""
        max_score = 10 * len(self.grade_report)
        grade_anti_score = 0.0
        for activity in self.grade_report.keys():
            # max_score += 10 * self.grade_report[activity]["grade"]
            # perda de score = (quao baixa eh a nota em relacao a mais alta) * media de notas da sala inteira
            class_grade_weight = self.grade_report[activity]["mean_grade"] / 10

            self.grades_sum += self.grade_report[activity]["grade"]

            grade_compared_to_highest = 10 - (
                self.grade_report[activity]["grade"]
                * 10
                / self.grade_report[activity]["highest_grade"]
            )
            grade_anti_score += grade_compared_to_highest * class_grade_weight

        return (max_score - grade_anti_score) / max_score * 100

    def compute_activity_completion_score(self):
        """Calcula o score associado a finalizacao de atividades."""
        # atividades importantes
        # e atividades nao importantes (que estao no report de notas)
        max_score = 0.0
        activity_anti_score = 0.0
        important_weight = 1.4
        self._compute_important_activities()
        for activity in self.grade_report.keys():
            completed = self.grade_report[activity]["completed"]
            is_important = self.grade_report[activity]["important"]
            # more weight to important activities
            activity_weight = important_weight if is_important else 1.0

            max_score += activity_weight
            activity_anti_score += (
                (activity_weight * self.grade_report[activity]["completion_rate"])
                if not completed
                else 0.0
            )

        return (max_score - activity_anti_score) / max_score * 100

    def _compute_important_activities(self):
        """Compute important activities.

        Activities are considered important if they are in the activity report.
        If they are important, assign them as so in the grade report.

        The name of the activity in the grade report is a substring of the name
        of the activity in the activity report.
        """
        if self.computed_important_activities:
            return
        self.computed_important_activities = True
        for activity in self.grade_report.keys():
            for important in self.activity_report.keys():
                if important in activity:
                    self.grade_report[activity]["important"] = True
                    break

    def interpolate_progression(self):
        """Interpola pontuacao para dias invalidos."""
        x = []
        y = []
        for index, datapoint in enumerate(self.progression):
            if datapoint is not None:
                x += [index]
                y += [datapoint]
        f = interp1d(x, y)

        xnew = [i for i in range(len(self.attendance_report))]
        ynew = f(xnew)

        return ynew

    def compute_attendance_score(self, interpolate: bool):
        """Compute student's attendance score."""
        report = self.attendance_report
        # self.missing_rate = []
        self.mean_scores = []
        self.max_score = []
        max_valid_score = []
        date_weights = []

        for index, date in enumerate(report.keys()):
            # TODO: no need to compute these attributes here, can be done from classroom
            # TODO: access attributes directly from parent class
            # self.missing_rate += [report[date]["missing_rate"]]
            self.mean_scores += [report[date]["mean_score"]]
            self.max_score += [report[date]["max_score"]]
            # do not compute days in which everyone was present
            if report[date]["valid"]:
                # progression += [(date, report[date]["score"])] # when date is datetime
                self.progression += [report[date]["score"]]
                max_valid_score += [report[date]["max_score"]]
                date_weights += [report[date]["mean_score"] / report[date]["max_score"]]
            elif index + 1 == len(report) and interpolate:
                # get last valid datapoint if very last datapoint is not valid
                # so that interpolation goes until last datapoint
                for i, data in enumerate(self.progression[::-1]):
                    if data is not None:
                        self.progression += [data]
                        date_weights += [
                            self.overall_mean_attendance_score
                            / report[date]["max_score"]
                        ]
                        break
            else:
                self.progression += [None]
                date_weights += [
                    self.overall_mean_attendance_score / report[date]["max_score"]
                ]

        if self.progression[0] is None and interpolate:
            # get mean score if very first datapoint is not valid
            # so that interpolation goes from the first datapoint
            self.progression[0] = np.mean(
                [i for i in self.progression if i is not None]
            )
            date_weights[0] = (
                self.overall_mean_attendance_score / report[date]["max_score"]
            )

        if interpolate:
            self.progression = self.interpolate_progression()

        weighted_anti_progression = []
        for index, data in enumerate(self.progression):
            if data is not None:
                weighted_anti_progression += [
                    (data * date_weights[index])
                    if data < self.max_score[index]
                    else self.max_score[index]
                ]

        self.weighted_progression = weighted_anti_progression
        attendance_score = (
            np.sum(weighted_anti_progression) / np.sum(max_valid_score) * 100
        )

        return attendance_score

    def _compute_progression(self):
        if self.progression != []:
            return
        if self.overall_mean_attendance_score is None:
            raise Exception("Overall mean attendance score not computed")
        for date in self.attendance_report.keys():
            # do not compute days in which everyone was present
            if self.attendance_report[date]["valid"]:
                self.progression += [self.attendance_report[date]["score"]]
            else:
                self.progression += [None]

    def compute_attributes(self):  # noqa
        # TODO: remove redundant attributes (not used in implicit analysis)
        # self.missing_rate = []
        self.mean_scores = []
        self.max_score = []
        for index, date in enumerate(self.attendance_report.keys()):
            # TODO: no need to compute these attributes here, can be done from classroom
            # TODO: access attributes directly from parent class
            # self.missing_rate += [self.attendance_report[date]["missing_rate"]]
            self.mean_scores += [self.attendance_report[date]["mean_score"]]
            self.max_score += [self.attendance_report[date]["max_score"]]
        missing_sequencial_count = 0

        self._reset_attributes()

        self._compute_progression()
        for index, score in enumerate(self.progression):
            if score is None:
                # continue # check which is better
                score = self.max_score[index]
            if score < self.mean_scores[index]:
                self.attendance_below_mean += 1
            else:
                self.attendance_above_mean += 1
            if score == 0.0:
                missing_sequencial_count += 1
                self.missing += 1
                # if self.missing_rate[index] not in self.missing_percentage.keys():
                #     self.missing_percentage[self.missing_rate[index]] = 0
                # self.missing_percentage[self.missing_rate[index]] += 1
            else:
                if missing_sequencial_count > 1:
                    if missing_sequencial_count not in self.sequencial_missing.keys():
                        self.sequencial_missing[missing_sequencial_count] = 0
                    self.sequencial_missing[missing_sequencial_count] += 1
                    # if missing_sequencial_count >= 3:
                    #     self.amount_sequencial_missing += 1
                missing_sequencial_count = 0
                if score == self.max_score[index]:
                    self.present += 1
                else:
                    self.partial_presence += 1

        self._compute_important_activities()
        for activity in self.grade_report.keys():
            self.grades_sum += self.grade_report[activity]["grade"]
            completed = self.grade_report[activity]["completed"]
            is_important = self.grade_report[activity]["important"]
            if completed:
                if is_important:
                    self.important_activities_complete += 1
                    if self.grade_report[activity]["completion_rate"] >= 0.5:
                        self.important_activities_complete_majority += 1
                    else:
                        self.important_activities_complete_minority += 1
                else:
                    self.activities_complete += 1
                    if self.grade_report[activity]["completion_rate"] >= 0.5:
                        self.activities_complete_majority += 1
                    else:
                        self.activities_complete_minority += 1
            else:
                if is_important:
                    self.important_activities_incomplete += 1
                    if self.grade_report[activity]["completion_rate"] >= 0.5:
                        self.important_activities_incomplete_majority += 1
                    else:
                        self.important_activities_incomplete_minority += 1
                else:
                    self.activities_incomplete += 1
                    if self.grade_report[activity]["completion_rate"] >= 0.5:
                        self.activities_incomplete_majority += 1
                    else:
                        self.activities_incomplete_minority += 1

            if 0 <= self.grade_report[activity]["grade"] <= 2.5:
                self.grades_between_0_2_5 += 1
                self.grades_below_5 += 1
            elif 2.5 < self.grade_report[activity]["grade"] <= 5:
                self.grades_between_2_5_5 += 1
                self.grades_below_5 += 1
            elif 5 < self.grade_report[activity]["grade"] <= 7.5:
                self.grades_between_5_7_5 += 1
                self.grades_above_5 += 1
            elif 7.5 < self.grade_report[activity]["grade"] <= 10:
                self.grades_between_7_5_10 += 1
                self.grades_above_5 += 1

            if (
                self.grade_report[activity]["grade"]
                < self.grade_report[activity]["mean_grade"]
            ):
                self.grades_below_mean += 1
            else:
                self.grades_above_mean += 1

    def _reset_attributes(self):  # noqa
        self.grades_between_0_2_5 = 0
        self.grades_between_2_5_5 = 0
        self.grades_between_5_7_5 = 0
        self.grades_between_7_5_10 = 0
        self.grades_below_5 = 0
        self.grades_above_5 = 0
        self.grades_below_mean = 0
        self.grades_above_mean = 0
        self.grades_sum = 0

        self.important_activities_complete = 0
        self.important_activities_complete_majority = 0
        self.important_activities_complete_minority = 0
        self.important_activities_incomplete = 0
        self.important_activities_incomplete_majority = 0
        self.important_activities_incomplete_minority = 0
        self.important_grades_below_mean = 0
        self.important_grades_above_mean = 0

        self.activities_complete = 0
        self.activities_complete_majority = 0
        self.activities_complete_minority = 0
        self.activities_incomplete = 0
        self.activities_incomplete_majority = 0
        self.activities_incomplete_minority = 0

        self.attendance_above_mean = 0
        self.attendance_below_mean = 0
        self.missing = 0
        self.present = 0
        self.partial_presence = 0
        # self.amount_sequencial_missing = 0
        # self.missing_percentage = {
        #     0.0: 0,
        #     10.0: 0,
        #     20.0: 0,
        #     30.0: 0,
        #     40.0: 0,
        #     50.0: 0,
        #     60.0: 0,
        #     70.0: 0,
        #     80.0: 0,
        #     90.0: 0,
        #     100.0: 0,
        # }

        self.sequencial_missing = {}
        for i in range(0, 501):
            self.sequencial_missing[i] = 0
