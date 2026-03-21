def can_view_student(user, student_profile):
    if user.role == "ADMIN":
        return True

    if user.role == "TEACHER":
        return True

    if user.role == "STUDENT":
        return student_profile.user == user

    if user.role == "PARENT":
        return student_profile in user.parentprofile.students.all()

    return False


def can_edit_student(user, student_profile):
    if user.role == "ADMIN":
        return True

    if user.role == "STUDENT":
        return student_profile.user == user

    return False