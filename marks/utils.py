from .models import ResultLock

def is_class_locked(class_name, exam_name="sem1"):
    try:
        lock = ResultLock.objects.get(
            class_name=class_name,
            exam_name=exam_name
        )
        return lock.is_locked
    except ResultLock.DoesNotExist:
        return False