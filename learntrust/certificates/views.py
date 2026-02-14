import hashlib
import qrcode
from qrcode.constants import ERROR_CORRECT_L
import io
from django.shortcuts import render, get_object_or_404
from django.conf import settings
from django.http import HttpResponse
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from .models import Certificate


def verify_certificate(request, verification_code):
    certificate = get_object_or_404(Certificate, verification_code=verification_code)
    
    # Check if certificate is revoked
    if certificate.is_revoked:
        return render(request, 'certificates/verify.html', {
            'certificate': certificate,
            'is_valid': False,
            'is_revoked': True
        })
    
    hash_input = f"{certificate.student_id}{certificate.course_id}{certificate.issued_at}{settings.SECRET_KEY}"
    recalculated_hash = hashlib.sha256(hash_input.encode()).hexdigest()
    
    is_valid = recalculated_hash == certificate.certificate_hash
    
    return render(request, 'certificates/verify.html', {
        'certificate': certificate,
        'is_valid': is_valid,
        'is_revoked': False
    })


def generate_certificate_pdf(request, certificate_id):
    """
    Generate certificate PDF with embedded QR code.
    """
    certificate = get_object_or_404(Certificate, id=certificate_id)
    
    # Generate verification URL
    verification_url = f"https://yourdomain.com/verify/{certificate.verification_code}/"
    
    # Generate QR code
    qr = qrcode.QRCode(
        version=1,
        error_correction=ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(verification_url)
    qr.make(fit=True)
    
    # Create QR code image
    qr_image = qr.make_image(fill_color="black", back_color="white")
    qr_buffer = io.BytesIO()
    qr_image.save(qr_buffer, format='PNG')
    qr_buffer.seek(0)
    
    # Create PDF
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="certificate_{certificate.certificate_id}.pdf"'
    
    p = canvas.Canvas(response, pagesize=letter)
    width, height = letter
    
    # Certificate title
    p.setFont("Helvetica-Bold", 24)
    p.drawCentredString(width/2, height - 100, "Certificate of Completion")
    
    # Certificate content
    p.setFont("Helvetica", 16)
    p.drawCentredString(width/2, height - 200, f"This certifies that")
    p.setFont("Helvetica-Bold", 20)
    p.drawCentredString(width/2, height - 240, certificate.student.username)
    p.setFont("Helvetica", 16)
    p.drawCentredString(width/2, height - 280, f"has successfully completed")
    p.setFont("Helvetica-Bold", 18)
    p.drawCentredString(width/2, height - 320, certificate.course.title)
    
    # Certificate ID and date
    p.setFont("Helvetica", 12)
    p.drawCentredString(width/2, height - 400, f"Certificate ID: {certificate.certificate_id}")
    p.drawCentredString(width/2, height - 420, f"Issued on: {certificate.issued_at.strftime('%B %d, %Y')}")
    
    # Add QR code
    p.drawImage(qr_buffer, width - 150, 50, width=100, height=100)
    
    # Add verification text
    p.setFont("Helvetica", 8)
    p.drawString(width - 150, 40, "Scan to verify")
    
    p.showPage()
    p.save()
    
    return response
