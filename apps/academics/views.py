import pandas as pd
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required, user_passes_test
from apps.users.models import User

def is_admin_or_staff(user):
    return user.is_authenticated and user.role in [User.Role.ADMIN, User.Role.STAFF]

@login_required
@user_passes_test(is_admin_or_staff)
def export_iemis_excel(request):
    """
    Queries student demographic data and outputs a formatted Excel file 
    matching CEHRD / IEMIS bulk upload column specifications.
    """
    # Fetch students with specific fields required by CEHRD
    students = User.objects.filter(role=User.Role.STUDENT).values(
        'username', 
        'first_name', 
        'last_name', 
        'citizenship_no', 
        'phone_number',
        'created_at'
    )
    
    # Convert QuerySet to Pandas DataFrame
    df = pd.DataFrame(list(students))
    
    if not df.empty:
        # Format dates to clean string representations
        if 'created_at' in df.columns:
            df['created_at'] = df['created_at'].dt.strftime('%Y-%m-%d')

        # Map internal database fields to official CEHRD IEMIS column headers
        df.rename(columns={
            'username': 'IEMIS Student ID / Roll',
            'first_name': 'First Name',
            'last_name': 'Last Name',
            'citizenship_no': 'Citizenship / Birth Reg No.',
            'phone_number': 'Guardian Contact',
            'created_at': 'Registration Date (AD)'
        }, inplace=True)
    else:
        # Generate empty dataframe with required headers if no records exist
        df = pd.DataFrame(columns=[
            'IEMIS Student ID / Roll', 'First Name', 'Last Name', 
            'Citizenship / Birth Reg No.', 'Guardian Contact', 'Registration Date (AD)'
        ])

    # Construct HttpResponse with Spreadsheet MIME type
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename="CEHRD_IEMIS_Student_Export_2081.xlsx"'

    # Stream Pandas DataFrame directly into HttpResponse via openpyxl
    with pd.ExcelWriter(response, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Student_Baseline_Data')

    return response