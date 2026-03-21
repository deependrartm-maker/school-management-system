def can_view_marks(user, student):
    if user.role == "ADMIN":
        return True

    if user.role == "TEACHER":
        return True

    if user.role == "STUDENT":
        return student.user == user

    if user.role == "PARENT":
        return student in user.parentprofile.students.all()

    return False
