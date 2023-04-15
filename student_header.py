import numpy as np
from scipy.interpolate import interp1d

class Student():
    """Student class.
    """
    def __init__(self, name: str, index: int) -> None:
        self.index = index
        self.name = name
        self.percentage = 0.0

        self.attendence_report = {}
        self.grade_report = {}
        self.activity_report = {}

        self.dropout = False
        self.dropout_truth = False

        self.score = 0.0
        self.max_score = 0.0
        self.predicted_score = 0.0
        self.truth_score = 0.0

        self.original_progression = []
        self.interpolated_progression = []

        self.chosen_progression = []
        self.chosen_progression_bool = []

    def compute_general_score(self):
        """Calcula a pontuacao geral do aluno no ranking.

        Leva em consideracao presenca (1/3), notas (1/3) e realizacao de atividades (1/3).
        """
        grade_score = self.compute_grade_score()
        completion_score = self.compute_activity_completion_score()
        attendence_score = self.compute_attendence_score()

        general_score = (
            (grade_score / 3)
            + (completion_score / 3)
            + (attendence_score / 3)
        )

        return general_score

    def compute_grade_score(self):
        """Calcula o score associado a notas e pesos atribuidos.
        """
        pass

    def compute_activity_completion_score(self):
        """Calcula o score associado a finalizacao de atividades.
        """
        pass
    
    def compute_attendence_score(self):
        """Compute student's attendence score.
        """
        for index, date in enumerate(self.attendence_report.keys()):
            self.max_score += self.attendence_report[date]["max_score"]
            self.truth_score += self.attendence_report[date]["score"]
            if self.attendence_report[date]["valid"]:
                # remove days in which everyone was present
                self.original_progression += [(index, self.attendence_report[date]["score"])]
            else:
                self.original_progression += [None]
        self.dropout_truth = self.truth_score / self.max_score < 0.75
        return np.sum([i[1] for i in self.original_progression if i is not None])
    
    def interpolate_attendence_score(self):
        """Interpola pontuacao para dias invalidos.
        """
        x = [i[0] for i in self.original_progression if i is not None]
        y = [i[1] for i in self.original_progression if i is not None]

        f = interp1d(x,y)

        xnew = [i for i in range(len(self.attendence_report)) if i < x[-1]]
        ynew = f(xnew)

        self.interpolated_progression = ynew
        return np.sum(ynew)
    
    def classify_dropout(self):
        """Classifica se estudante desistiu.
        """
        count_drops = 0
        for datapoint in self.chosen_progression_bool:
            if not datapoint:
                count_drops += 1
            else:
                count_drops = 0
            if count_drops == 3: #mudei de 5 para 3 e ficou melhor, 4 tem alguns falsos negativos ainda
                self.dropout = True
                break

    def define_chosen_method(self):
        """
        """
        # self.chosen_progression = [i[1] for i in self.original_progression if i is not None]
        self.chosen_progression = self.interpolated_progression