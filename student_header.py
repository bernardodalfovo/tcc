import numpy as np
from scipy.interpolate import interp1d

class Student():
    """Student class.
    """
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
    
    def compute_score(self):
        """Compute student's attendence score.
        """
        for index, date in enumerate(self.reports.keys()):
            self.max_score += self.reports[date]["max_score"]
            if self.reports[date]["valid"]:
                # remove days in which everyone was present
                self.progression += [(index, self.reports[date]["score"])]

        self.score = np.sum(self.progression)
    
    def interpolate_score(self):
        """Interpola pontuacao para dias invalidos.
        """
        x = [i[0] for i in self.progression]
        y = [i[1] for i in self.progression]

        f = interp1d(x,y)

        xnew = range(len(x))
        ynew = f(xnew)

        self.interpolated_progression = ynew
        return sum(ynew)
    
    def classify_dropout(self):
        """Classifica se estudante desistiu.
        """
        count_drops = 0
        for datapoint in self.interpolated_progression_bool:
            if not datapoint:
                count_drops += 1
            else:
                count_drops = 0
            if count_drops == 5:
                self.drop_out = True
                break