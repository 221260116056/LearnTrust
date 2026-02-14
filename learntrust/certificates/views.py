import hashlib
from django.shortcuts import render, get_object_or_404
from django.conf import settings
from .models import Certificate


def verify_certificate(request, verification_code):
    try:
        certificate = Certificate.objects.get(verification_code=verification_code)
        
        hash_input = f"{certificate.student_id}{certificate.course_id}{certificate.issued_at}{settings.SECRET_KEY}"
        recalculated_hash = hashlib.sha256(hash_input.encode()).hexdigest()
        
        is_valid = recalculated_hash == certificate.certificate_hash
        
        return render(request, 'certificates/verify.html', {
            'certificate': certificate,
            'is_valid': is_valid
        })
    except Certificate.DoesNotExist:
        return render(request, 'certificates/verify.html', {
            'certificate': None,
            'is_valid': False
        })
