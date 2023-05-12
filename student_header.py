import numpy as np
from scipy.interpolate import interp1d

class Student():
    """Student class.
    """
    def __init__(self, name: str, index: int) -> None:
        self.index = index
        self.name = name
        self.percentage = 0.0

        self.progression = []
        self.weighted_progression = []

        self.attendance_report = {}
        self.grade_report = {}
        self.activity_report = {}

        self.general_score = 0.0
        self.activity_score = 0.0
        self.attendance_score = 0.0
        self.overall_mean_attendance_score = 0.0

    def compute_general_score(self, interpolate_attendance: bool):
        """Calcula a pontuacao geral do aluno no ranking.

        Leva em consideracao presenca (1/3), notas (1/3) e realizacao de atividades (1/3).
        """
        grade_score = self.compute_grade_score()
        completion_score = self.compute_activity_completion_score()
        attendance_score = self.compute_attendance_score(interpolate=interpolate_attendance)

        # print(f"{self.name}, Grade: {round(grade_score, 2)}, Important activities: {round(completion_score, 2)}, attendance: {round(attendance_score, 2)}")

        general_score = (
            (grade_score / 3)
            + (completion_score / 3)
            + (attendance_score / 3)
        )
        self.general_score = general_score
        return general_score

    def compute_grade_score(self):
        """Calcula o score associado a notas e pesos atribuidos.
        """
        max_score = 10 * len(self.grade_report)
        grade_anti_score = 0.0
        for activity in self.grade_report.keys():
            # max_score += 10 * self.grade_report[activity]["grade"]
            # perda de score = (quao baixa eh a nota em relacao a mais alta) * media de notas da sala inteira
            class_grade_weight = self.grade_report[activity]["mean_grade"] / 10
            grade_compared_to_highest = (10 - (self.grade_report[activity]["grade"] * 10 / self.grade_report[activity]["highest_grade"]))
            grade_anti_score += grade_compared_to_highest * class_grade_weight
        
        return (max_score - grade_anti_score) / max_score * 100

    def compute_activity_completion_score(self):
        """Calcula o score associado a finalizacao de atividades.
        """
        # atividades importantes
        # e atividades nao importantes (que estao no report de notas)
        max_score = 0.0
        activity_anti_score = 0.0
        important_weight = 1.4
        for activity in self.grade_report.keys():
            completed = self.grade_report[activity]["completed"]
            is_important = False
            for important in self.activity_report.keys():
                if important in activity:
                    is_important = True
                    break
            # more weight to important activities
            activity_weight = important_weight if is_important else 1.0

            max_score += activity_weight
            activity_anti_score += (activity_weight * self.grade_report[activity]["completion_rate"]) if not completed else 0.0
            
        return (max_score - activity_anti_score) / max_score * 100

    
    def compute_attendance_score(self, interpolate: bool):
        """Compute student's attendance score.
        """
        report = self.attendance_report
        max_score = []
        max_valid_score = []
        date_weights = []
        progression = []

        for index, date in enumerate(report.keys()):
            max_score += [report[date]["max_score"]]
            # do not compute days in which everyone was present
            if report[date]["valid"]:
                # progression += [(date, report[date]["score"])] # when date is datetime
                progression += [report[date]["score"]]
                max_valid_score += [report[date]["max_score"]]
                date_weights += [report[date]["mean_score"] / report[date]["max_score"]]
            elif index+1 == len(report) and interpolate:
                # get last valid datapoint if very last datapoint is not valid
                # so that interpolation goes until last datapoint
                for i, data in enumerate(progression[::-1]):
                    if data is not None:
                        progression += [data]
                        date_weights += [self.overall_mean_attendance_score / report[date]["max_score"]]
            else:
                progression += [None]
                date_weights += [self.overall_mean_attendance_score / report[date]["max_score"]]
        if progression[0] is None and interpolate:
                # get mean score if very first datapoint is not valid
                # so that interpolation goes from the first datapoint
                progression[0] = np.mean([i for i in progression if i is not None])
                date_weights[0] = self.overall_mean_attendance_score / report[date]["max_score"]
        if interpolate:
            progression = self.interpolate_progression(progression=progression)

        self.progression = progression

        weighted_anti_progression = []
        for index, data in enumerate(progression):
            if data is not None:
                weighted_anti_progression += [(data * date_weights[index]) if data < max_score[index] else max_score[index]]
        
        self.weighted_progression = weighted_anti_progression

        attendance_score = np.sum(weighted_anti_progression) / np.sum(max_score if interpolate else max_valid_score) * 100

        return attendance_score
    
    def interpolate_progression(self, progression: list):
        """Interpola pontuacao para dias invalidos.
        """
        x = []
        y = []
        for index, datapoint in enumerate(progression):
            if datapoint is not None:
                x += [index]
                y += [datapoint]
                # x += [datapoint[0]]     # datetime
                # y += [datapoint[1]]     # score
        f = interp1d(x,y)

        xnew = [i for i in range(len(self.attendance_report))]
        ynew = f(xnew)

        return ynew
    
    def classify_dropout(self):
        """Classifica se estudante desistiu.
        """
        count_drops = 0
        for datapoint in self.chosen_progression_bool:
            if not datapoint:
                count_drops += 1
            else:
                count_drops = 0
            if count_drops == 3:
                self.dropout = True
                break