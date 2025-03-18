from django.urls import path
from .views import *
from rest_framework.authtoken.views import obtain_auth_token


urlpatterns = [
    path('adminlogin/',admin_login),
    path('map_superuser_to_admin/', map_superuser_to_admin),
    path('admin/',add_admin),
    path('login/', login_user, name='login'), 
    path('employee_login/',employee_login,name='employee_login') ,# Get Token
    path('logout/', logout_user, name='logout'),      # Remove Token


    path('employee_dashboard/', employee_dashboard),
    path('new_travel_request/', new_travel_request),
    path('edit_travel_request/<int:request_id>/', edit_travel_request),
    path('delete_travel_request/<int:request_id>/', delete_travel_request),

    path('manager_dashboard/', manager_dashboard),
    path('filter_sort_search/', filter_sort_search),
    path('manager_status_update/', manager_status_update),

    path('admin_dashboard/', admin_dashboard),
    path('add_manager/', add_manager),
    path('edit_manager/<int:manager_id>/',edit_manager),
    path('delete_manager/<int:manager_id>/',delete_manager),
    path('add_employee/', add_employee),
    path('edit_employee/<int:employee_id>/',edit_employee),
    path('delete_employee/<int:employee_id>/',delete_manager),
    path('admin_status_update/',admin_status_update),
    path('close_ticket/',close_ticket),
    path('list_employees/',list_employees),
    path('list_managers/',list_managers)
]
