import csv
import io
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from student.models import Course, Module
from student.decorators import role_required
from .models import ImmutableLog


def export_logs_as_csv(logs, course):
    """
    Export logs as CSV file.
    """
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write headers
    writer.writerow([
        'Timestamp',
        'User',
        'Module',
        'Event Type',
        'Metadata',
        'Token Hash',
        'Previous Hash',
        'Current Hash'
    ])
    
    # Write data
    for log in logs:
        writer.writerow([
            log.timestamp.isoformat(),
            log.user.username,
            str(log.module) if log.module else 'N/A',
            log.event_type,
            str(log.metadata),
            log.token_hash,
            log.previous_hash,
            log.current_hash
        ])
    
    return output.getvalue()


def export_logs_as_pdf(logs, course):
    """
    Export logs as PDF file.
    """
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    
    # Title
    p.setFont("Helvetica-Bold", 16)
    p.drawString(50, height - 50, f"Audit Logs - {course.title}")
    
    # Headers
    p.setFont("Helvetica-Bold", 10)
    y = height - 80
    headers = ['Timestamp', 'User', 'Event', 'Module']
    x_positions = [50, 180, 280, 380]
    for i, header in enumerate(headers):
        p.drawString(x_positions[i], y, header)
    
    # Data rows
    p.setFont("Helvetica", 8)
    y -= 20
    
    for log in logs:
        if y < 50:  # New page
            p.showPage()
            y = height - 50
            p.setFont("Helvetica", 8)
        
        p.drawString(50, y, log.timestamp.strftime('%Y-%m-%d %H:%M'))
        p.drawString(180, y, log.user.username[:15])
        p.drawString(280, y, log.event_type[:20])
        p.drawString(380, y, str(log.module)[:25] if log.module else 'N/A')
        
        y -= 15
    
    p.showPage()
    p.save()
    
    buffer.seek(0)
    return buffer


@login_required
@role_required('teacher')
def export_logs(request, course_id):
    """
    Export ImmutableLog entries for a course.
    """
    course = get_object_or_404(Course, id=course_id)
    export_format = request.GET.get('format', 'csv')
    
    # Get all logs for this course's modules
    module_ids = Module.objects.filter(course=course).values_list('id', flat=True)
    logs = ImmutableLog.objects.filter(module_id__in=module_ids).order_by('-timestamp')
    
    if export_format == 'csv':
        csv_content = export_logs_as_csv(logs, course)
        response = HttpResponse(csv_content, content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="logs_{course.id}.csv"'
        return response
    
    elif export_format == 'pdf':
        pdf_buffer = export_logs_as_pdf(logs, course)
        response = HttpResponse(pdf_buffer.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="logs_{course.id}.pdf"'
        return response
    
    else:
        return HttpResponse("Invalid format. Use 'csv' or 'pdf'.", status=400)
