from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .forms import TaskSubmissionFormSet
from .models import TaskSubmission, Engineer, InventoryItem
from django.db.models import Count, Q
from django.http import HttpResponse
import pandas as pd
from weasyprint import HTML
import io
from django.utils import timezone
from datetime import datetime
from django.contrib.auth.decorators import user_passes_test
import os

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
        if formset.is_valid():
            saved_tasks = []
            for form in formset.forms:
                if form.cleaned_data and not form.cleaned_data.get('DELETE', False):
                    task = form.save(commit=False)
                    if hasattr(request.user, 'engineer') and request.user.engineer:
                        task.engineer = request.user.engineer
                        if not task.reporter:
                            task.reporter = request.user.engineer.name
                        if not task.date:
                            task.date = timezone.now().date()
                        task.save()
                        form.save_m2m()
                        # If reporter is blank or equals the primary engineer, append team members to it
                        if hasattr(request.user, 'engineer'):
                            names = [request.user.engineer.name] + [m.name for m in task.team_members.all()]
                            if not task.reporter or task.reporter.strip() == request.user.engineer.name.strip():
                                task.reporter = ", ".join(names)
                                task.save(update_fields=['reporter'])
                        saved_tasks.append(task)
            if saved_tasks:
                return redirect('reports:submission_confirmation')
    else:
        initial = []
        if hasattr(request.user, 'engineer'):
            initial.append({
                'date': timezone.now().date(),
                'reporter': request.user.engineer.name,
            })
        formset = TaskSubmissionFormSet(initial=initial or None)
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
    # Exclude team leaders from the engineers list shown in the table
    engineers = Engineer.objects.filter(is_team_leader=False)
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
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    from openpyxl.utils import get_column_letter

    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    tasks = TaskSubmission.objects.select_related('engineer').prefetch_related('team_members').all()
    if date_from and date_to:
        try:
            start_date = datetime.strptime(date_from, '%Y-%m-%d').replace(hour=0, minute=0, second=0)
            end_date = datetime.strptime(date_to, '%Y-%m-%d').replace(hour=23, minute=59, second=59)
            tasks = tasks.filter(submitted_at__range=[start_date, end_date])
        except ValueError:
            pass

    et_green = "008751"
    et_yellow = "FFC107"

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        primary_ids = tasks.values_list('engineer_id', flat=True)
        member_ids = tasks.values_list('team_members__id', flat=True)
        all_ids = {i for i in primary_ids if i is not None} | {i for i in member_ids if i is not None}
        engineers = Engineer.objects.filter(id__in=all_ids)
        for engineer in engineers:
            eng_tasks = tasks.filter(Q(engineer=engineer) | Q(team_members=engineer)).distinct()
            rows = []
            for t in eng_tasks:
                rows.append({
                    'date': t.date,
                    'shift': t.shift,
                    'reporter': t.reporter or engineer.name,
                    'location': t.location,
                    'equipment_type': t.equipment_type,
                    'problem_description': t.description,
                    'cause_of_problem': t.cause_of_problem,
                    'corrective_action': t.corrective_measure,
                    'start_time': timezone.make_naive(t.start_time, timezone.get_default_timezone()) if t.start_time and timezone.is_aware(t.start_time) else t.start_time,
                    'end_time': timezone.make_naive(t.end_time, timezone.get_default_timezone()) if t.end_time and timezone.is_aware(t.end_time) else t.end_time,
                    'time_taken': t.time_taken,
                    'status': t.status,
                    'remark': t.remark,
                })
            df = pd.DataFrame(rows)
            if df.empty:
                df = pd.DataFrame(columns=[
                    'date','shift','reporter','location','equipment_type','problem_description',
                    'cause_of_problem','corrective_action','start_time','