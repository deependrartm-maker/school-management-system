def can_view_attendance(user, student):
    if user.role == 'ADMIN':
        return True

    if user.role == 'TEACHER':
        return True

    if user.role == 'STUDENT':
        return hasattr(user, 'studentprofile') and user.studentprofile == student

    if user.role == 'PARENT':
        return hasattr(user, 'parentprofile') and student in user.parentprofile.students.all()

    return False