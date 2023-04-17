import numpy as np
from student_header import Student

class Classroom():
    def __init__(self, attendence_report_doc: any, grade_report_doc: any, activity_report_doc: any) -> None:
        self.students = {}
        # self.attendence_weights = []
        # self.mean_attendence_score = 0.0

        self.attendence_report = attendence_report_doc
        self.grade_report = grade_report_doc
        self.activity_report = activity_report_doc

        for index, name in attendence_report_doc["Nome"].items():
            self.students[index] = Student(name=name, index=index)
    
    # def measure_weights_attendence(self):
    #     """Calcula os pesos de cada falta baseado na turma inteira
    #     """
    #     weight_array = []
    #     for index_date in range(len(self.students[1].chosen_progression)):
    #         weight_date = []
    #         for _, student in self.students.items():
    #             if student.original_progression[index_date] is not None:
    #                 weight_date += [student.chosen_progression[index_date]]
    #             elif len(student.chosen_progression) != len(student.original_progression):
    #                 weight_date += [self.mean_attendence_score]
    #         weight_array += [weight_date]
    #     weight_array_new = []
    #     for date in weight_array:
    #         weight_array_new += [np.mean(date)]
    #     self.attendence_weights = np.array(weight_array_new)

    # def measure_weights_atividades(self):
    #     """Calcula peso para cada atividade realizada pela turma, em relacao a faltas.
        
    #     Leva em consideracao atividades classificadas como importantes.

    #     Atividades importantes apresentam 40% mais peso que nao importantes.
    #     """
    #     print(self.activity_report)
    #     pass
    
    # def measure_weights_notas(self):
    #     """Calcula peso para cada atividade realizada pela turma, em relacao a notas.

        
    #     """
    #     pass

    # def compute_mean_attendence_score(self):
    #     """Calcula a media das pontuacoes relacionadas a presenca da sala.
    #     """
    #     sum_score = []
    #     for index, student in self.students.items():
    #         sum_score += [student.attendence_score / len([i for i in student.original_progression if i is not None])]
    #     self.mean_attendence_score = np.mean(sum_score)