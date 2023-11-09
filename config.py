ratio_evaluation = [1.0, 0.75, 0.5, 0.25]
analysis_repeat = 10
relative_class = False
test_size = 0.2

n_best_features = [5, 10]

attendance_sheet_name = "presenca"
grade_sheet_name = "notas"
activity_sheet_name = "importantes"

sheets = {
    # "1WbqYKXmMg4vkyROidhdEsTEaZLPLkySbbTJqSZKTuKQ", # fake, grades, attendence and important activities
    "turma_1": "1Ol0xuLtDwJw4CndlL__dwKI0cDY3aCvA-ELrBotKn3E",
    "turma_2": "1SAY_0d6xP_SffE5kvjmzYPPDRjAm1iLjmXsZ1n6Uzvo",
}

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
