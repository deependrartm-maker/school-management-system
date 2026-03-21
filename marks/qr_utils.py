import hashlib
from django.conf import settings


def generate_verification_token(admission_no, exam_name):
    raw_string = f"{admission_no}:{exam_name}:{settings.SECRET_KEY}"
    
    signature = hashlib.sha256(raw_string.encode()).hexdigest()
    
    token = f"{admission_no}_{exam_name}_{signature}"
    
    return token