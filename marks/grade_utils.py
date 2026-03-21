def calculate_grade(percentage):
    if percentage >= 90:
        return "A+"
    elif percentage >= 80:
        return "A"
    elif percentage >= 70:
        return "B+"
    elif percentage >= 60:
        return "B"
    elif percentage >= 50:
        return "C"
    elif percentage >= 40:
        return "D"
    else:
        return "F"
def calculate_pass_fail(mark_records):
    """
    Returns: (status, overall_percentage)
    """
    if not mark_records:
        return "FAIL", 0

    total_obtained = 0
    total_max = 0

    for record in mark_records:
        subject_percentage = (record.marks_obtained / record.total_marks) * 100
        if subject_percentage < 33:
            return "FAIL", 0

        total_obtained += record.marks_obtained
        total_max += record.total_marks

    overall_percentage = (total_obtained / total_max) * 100

    if overall_percentage < 33:
        return "FAIL", overall_percentage

    return "PASS", overall_percentage


def calculate_division(percentage):
    if percentage >= 60:
        return "First Division"
    elif percentage >= 45:
        return "Second Division"
    elif percentage >= 33:
        return "Third Division"
    return "Fail"


def calculate_class_ranks(students_data):
    """
    students_data format:
    [
        {"student_id": 1, "percentage": 75.4},
        {"student_id": 2, "percentage": 63.2},
        ...
    ]
    Returns:
    {student_id: rank}
    """

    sorted_students = sorted(
        students_data,
        key=lambda x: x["percentage"],
        reverse=True
    )

    ranks = {}
    current_rank = 1

    for index, student in enumerate(sorted_students):
        if index > 0 and student["percentage"] < sorted_students[index - 1]["percentage"]:
            current_rank = index + 1

        ranks[student["student_id"]] = current_rank

    return ranks