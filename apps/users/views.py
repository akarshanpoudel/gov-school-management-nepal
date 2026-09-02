import csv
import io
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils.crypto import get_random_string
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
        # Each new student gets their own random, single-use temporary
        # password instead of a school-wide default. A shared password
        # like "student123" means anyone who knows the pattern (a former
        # student, a leaked handout) can log in as *any* student. The
        # generated values are shown once below so an admin can hand them
        # out securely; they are never stored or logged in plaintext.
        new_credentials = []
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
                    temp_password = get_random_string(10)
                    user.set_password(temp_password)
                    user.save()
                    created_count += 1
                    new_credentials.append({'username': username, 'password': temp_password})

        if created_count:
            messages.success(request, f'Successfully imported {created_count} new students!')
        else:
            messages.warning(request, 'No new students were imported (usernames may already exist, or the file was empty).')

        return render(request, 'users/bulk_import.html', {'new_credentials': new_credentials})

    return render(request, 'users/bulk_import.html')