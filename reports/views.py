from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .forms import TaskSubmissionFormSet
from .models import TaskSubmission, Engineer
from django.db.models import Count
from django.http import HttpResponse
import pandas as pd
from weasyprint import HTML
import io
from django.utils import timezone
from datetime import datetime
from django.contrib.auth.decorators import user_passes_test
import os  # Added to fix NameError in export_pdf

# Custom decorator to check if user is a team leader
def team_leader_required(view_func):
    def _wrapped_view(request, *args, **kwargs):
        if not hasattr(request.user, 'engineer') or not request.user.engineer.is_team_leader:
            return HttpResponse("You do not have permission to access this page.", status=403)
        return view_func(request, *args, **kwargs)
    return _wrapped_view

@login_required
def submit_tasks(request):
    if request.method == 'POST':
        formset = TaskSubmissionFormSet(request.POST)
        print("POST request received. Raw POST data:", request.POST)
        if formset.is_valid():
            print("Formset is valid. Processing forms...")
            saved_tasks = []
            for i, form in enumerate(formset.forms):
                if form.cleaned_data and not form.cleaned_data.get('DELETE', False):
                    task = form.save(commit=False)
                    if hasattr(request.user, 'engineer') and request.user.engineer:
                        task.engineer = request.user.engineer
                        task.save()
                        form.save_m2m()
                        saved_tasks.append(task)
                        print(f"Task {i} saved with ID: {task.id}")
                    else:
                        print(f"Error for task {i}: No engineer associated with user: {request.user.username}")
            if saved_tasks:
                print("All tasks saved successfully. Redirecting to confirmation.")
                return redirect('reports:submission_confirmation')
            else:
                print("No tasks saved. Possible validation or engineer issue.")
        else:
            print("Formset is invalid. Errors by form index:", {i: form.errors for i, form in enumerate(formset.forms)})
    else:
        formset = TaskSubmissionFormSet()
        print("GET request. Initializing empty formset.")
    return render(request, 'submit_tasks.html', {'formset': formset})

@login_required
def submission_confirmation(request):
    return render(request, 'submission_confirmation.html')

@team_leader_required
@login_required
def dashboard(request):
    selected_date = request.GET.get('date')
    tasks = TaskSubmission.objects.all().order_by('-submitted_at')
    unique_dates = TaskSubmission.objects.dates('submitted_at', 'day', order='DESC')
    
    if selected_date:
        tasks = tasks.filter(submitted_at__date=selected_date)
    
    summary = tasks.values('engineer__et_id', 'engineer__name', 'task_type').annotate(count=Count('task_type'))
    engineers = Engineer.objects.all()
    task_details = tasks.select_related('engineer').prefetch_related('team_members')
    
    return render(request, 'dashboard.html', {
        'summary': summary,
        'engineers': engineers,
        'task_details': task_details,
        'unique_dates': unique_dates,
        'selected_date': selected_date,
    })

@login_required
def export_excel(request):
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    tasks = TaskSubmission.objects.all()
    if date_from and date_to:
        try:
            start_date = datetime.strptime(date_from, '%Y-%m-%d').replace(hour=0, minute=0, second=0)
            end_date = datetime.strptime(date_to, '%Y-%m-%d').replace(hour=23, minute=59, second=59)
            tasks = tasks.filter(submitted_at__range=[start_date, end_date])
        except ValueError:
            pass
    
    summary_data = tasks.values('engineer__et_id', 'engineer__name', 'task_type').annotate(count=Count('task_type'))
    df_summary = pd.DataFrame(list(summary_data))
    df_summary = df_summary.pivot_table(index=['engineer__et_id', 'engineer__name'], columns='task_type', values='count', fill_value=0)
    df_summary['Total'] = df_summary.sum(axis=1)
    
    tasks_data = tasks.values('submitted_at', 'engineer__et_id', 'engineer__name', 'task_type', 'description', 'equipment_type', 'team_members__name')
    for task in tasks_data:
        if task['submitted_at'] and timezone.is_aware(task['submitted_at']):
            task['submitted_at'] = timezone.make_naive(task['submitted_at'], timezone.get_default_timezone())
    
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_summary.to_excel(writer, sheet_name='Summary', index=True)
        df_tasks = pd.DataFrame(list(tasks_data))
        df_tasks.to_excel(writer, sheet_name='Details', index=False)
        
        # Adjust column widths for both sheets using the same logic as Details
        workbook = writer.book
        for sheet_name in ['Summary', 'Details']:
            worksheet = writer.sheets[sheet_name]
            df = df_summary if sheet_name == 'Summary' else df_tasks
            for i, col in enumerate(worksheet.columns):
                # Get the column letter (A, B, C, ...)
                column_letter = chr(65 + i)
                # Calculate max length based on the first row (header) and data
                max_length = 0
                for cell in col:
                    if cell.value:
                        cell_length = len(str(cell.value))
                        max_length = max(max_length, cell_length)
                # Ensure at least the header length is considered
                header_length = len(str(worksheet.cell(row=1, column=i+1).value)) if worksheet.cell(row=1, column=i+1).value else 0
                max_length = max(max_length, header_length) + 2
                worksheet.column_dimensions[column_letter].width = max_length

    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename=task_summary.xlsx'
    response.write(output.getvalue())
    return response

@login_required
def export_pdf(request):
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    tasks = TaskSubmission.objects.all()
    if date_from and date_to:
        try:
            start_date = datetime.strptime(date_from, '%Y-%m-%d').replace(hour=0, minute=0, second=0)
            end_date = datetime.strptime(date_to, '%Y-%m-%d').replace(hour=23, minute=59, second=59)
            tasks = tasks.filter(submitted_at__range=[start_date, end_date])
        except ValueError:
            pass
    
    summary = tasks.values(
        'engineer__et_id', 'engineer__name', 'task_type',
        'submitted_at', 'shift', 'location', 'equipment_type',
        'description', 'cause_of_problem', 'corrective_measure',
        'start_time', 'end_time'
    ).annotate(count=Count('task_type'))
    engineers = Engineer.objects.all()
    
    totals = [{'et_id': engineer.et_id, 'total': sum(count['count'] for count in summary if count['engineer__et_id'] == engineer.et_id)} for engineer in engineers]
    
    html = render(request, 'pdf_template.html', {'summary': summary, 'engineers': engineers, 'totals': totals}).content.decode('utf-8')
    
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename=task_summary.pdf'
    HTML(string=html, base_url=request.build_absolute_uri()).write_pdf(response, stylesheets=['/static/css/pdf_styles.css'] if os.path.exists('/static/css/pdf_styles.css') else [])
    return response