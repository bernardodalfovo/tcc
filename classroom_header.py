import numpy as np
from student_header import Student

class Classroom():
    def __init__(self, report_doc: any) -> None:
        self.students = {}
        self.weights = []
        for index, name in report_doc["Nome"].items():
            self.students[index] = Student(name=name, index=index)
    
    def measure_weights(self):
        """Calcula os pesos de cada falta baseado na turma inteira
        """
        weight_array = []
        for index_date in range(len(self.students[1].interpolated_progression)):
            weight_date = []
            for _, student in self.students.items():
                weight_date += [student.interpolated_progression[index_date]]
            weight_array += [weight_date]
        weight_array_new = []
        for date in weight_array:
            weight_array_new += [np.mean(date)]
        self.weights = np.array(weight_array_new)