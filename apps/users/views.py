import csv
import io
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from apps.users.models import User
from apps.academics.models import ClassRoom
from apps.users.decorators import role_required

@login_required
@role_required(User.Role.ADMIN)
def bulk_student_import_view(request):
    if request.method == 'POST' and request.FILES.get('csv_file'):
        csv_file = request.FILES['csv_file']
        
        if not csv_file.name.endswith('.csv'):
            messages.error(request, 'Please upload a valid CSV file.')
            return redirect('users:bulk_import')

        decoded_file = csv_file.read().decode('utf-8')
        io_string = io.StringIO(decoded_file)
        reader = csv.DictReader(io_string)

        created_count = 0
        for row in reader:
            username = row.get('username', '').strip()
            first_name = row.get('first_name', '').strip()
            last_name = row.get('last_name', '').strip()
            classroom_name = row.get('classroom', '').strip()

            classroom = ClassRoom.objects.filter(name=classroom_name).first() if classroom_name else None

            if username:
                user, created = User.objects.get_or_create(
                    username=username,
                    defaults={
                        'first_name': first_name,
                        'last_name': last_name,
                        'role': User.Role.STUDENT,
                        'classroom': classroom,
                    }
                )
                if created:
                    user.set_password('student123')
                    user.save()
                    created_count += 1

        messages.success(request, f'Successfully imported {created_count} new students!')
        return redirect('core:dashboard')

    return render(request, 'users/bulk_import.html')