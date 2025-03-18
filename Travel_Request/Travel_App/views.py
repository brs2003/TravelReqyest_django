from django.shortcuts import render,get_object_or_404
from django.contrib.auth import authenticate
from rest_framework.decorators import api_view,permission_classes
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND,HTTP_401_UNAUTHORIZED
from .models import Employee,Admin,Manager,Employee_Request
from .serializers import TicketRequestSerializer,EmployeeTableSerializer,EmployeeNameSerializer,ManagerNameSerializer,ManagerTableSerializer,AdminTableSerializer,ManagerSerializer,EmployeeSerializer
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from django.contrib.auth.models import User
from django.db.models import Q
from .permissions import IsAdminUser, IsManagerUser, IsEmployeeUser
from django.contrib.auth.models import User, Group
from rest_framework.permissions import IsAuthenticated,AllowAny
from rest_framework.authtoken.models import Token
from django.utils.timezone import now 
from rest_framework import status
from django.core.mail import send_mail
from datetime import datetime,date
import logging

logger = logging.getLogger(__name__)

@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
def employee_login(request):
    """
    Authenticate an admin and return a token if credentials are valid.
    """
    if request.method == 'POST':
        data = json.loads(request.body)
        user = authenticate(username=data['username'], password=data['password'])
        if user is not None and hasattr(user,'employee'):
            token, created = Token.objects.get_or_create(user=user)
            logger.info(f"Employee {user.username} logged in successfully.")
            return JsonResponse({'status': 'success', 'token': token.key})
        logger.warning(f"Failed login attempt for username: {data['username']}")
        return JsonResponse({'status': 'failed', 'message': 'Invalid credentials'}, status=401)
    logger.error("Invalid request method for employee_login")
    return JsonResponse({'status': 'failed', 'message': 'Invalid request method'}, status=400)    


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsEmployeeUser])
def employee_dashboard(request):
    try:
        # Get the authenticated user
        user = request.user
        # Retrieve the employee associated with the authenticated user
        employee = Employee.objects.filter(user_auth=user).first()
        if not employee:
            logger.error(f"Invalid Employee for user: {user.username}")
            return Response({"error": "Invalid Employee"}, status=status.HTTP_404_NOT_FOUND)
        # Get the employee's travel requests
        req = Employee_Request.objects.filter(employee=employee)
        serializer = EmployeeTableSerializer(req, many=True)
        
        logger.info(f"Employee {user.username} accessed their dashboard.")
        return Response(serializer.data, status=status.HTTP_200_OK)
    except Employee_Request.DoesNotExist:
        logger.error(f"No requests found for employee: {user.username}")
        return Response({"error": "No requests found"}, status=status.HTTP_404_NOT_FOUND) 

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def new_travel_request(request):
    try:
        data = request.data
        user = request.user

        # Validate Employee
        employee = Employee.objects.filter(user_auth=user).first()
        if not employee:
            logger.error(f"Invalid Employee for user: {user.username}")
            return Response({"status": "failed", "message": "Invalid Employee"}, status=status.HTTP_404_NOT_FOUND)

        # Validate Manager ID (optional)
        manager = employee.manager  # Assuming Employee has a ForeignKey to Manager
        if not manager:
            logger.error(f"Manager not assigned for employee: {user.username}")
            return Response({"status": "failed", "message": "Manager not assigned"}, status=status.HTTP_404_NOT_FOUND)

        # Create a new travel request entry
        new_ticket = Employee_Request.objects.create(
            employee=employee,  
            manager=manager,  
            date_of_sub=data.get("date_of_sub", date.today()),  # Default to today
            purpose=data.get("purpose"),
            from_loc=data.get("from_loc"),
            to_loc=data.get("to_loc"),
            travel_mode=data.get("travel_mode"),
            from_date=data.get("from_date"),
            to_date=data.get("to_date"),
            lodging_required=data.get("lodging_required", "No"),
            additional_request=data.get("additional_request", ""),
            manager_note=data.get("manager_note", ""),
            admin_note=data.get("admin_note", ""),
            no_of_resub=data.get("no_of_resub", 1),
            manager_status=data.get("manager_status", "Pending"),
            admin_status=data.get("admin_status", "Not_closed"),
        )

        logger.info(f"New travel request created by employee: {user.username}")
        return Response(
            {"status": "success", "message": "Travel request created successfully", "ticket_id": new_ticket.id},
            status=status.HTTP_201_CREATED
        )

    except Exception as e:
        logger.error(f"Error creating travel request for employee: {user.username} - {str(e)}")
        return Response({"status": "failed", "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)


#Edit Travel Request
@csrf_exempt
@permission_classes([IsAuthenticated, IsEmployeeUser])
@api_view(['PUT'])
def edit_travel_request(request, request_id):
    travel_request = get_object_or_404(Employee_Request, id=request_id)

    try:
        data = json.loads(request.body)  
    except json.JSONDecodeError:
        logger.error("Invalid JSON format in edit_travel_request")
        return Response({"error": "Invalid JSON"}, status=HTTP_400_BAD_REQUEST)

    serializer = EmployeeTableSerializer(travel_request, data=data, partial=True)

    if serializer.is_valid():
        serializer.save()
        logger.info(f"Travel request {request_id} updated by employee: {request.user.username}")
        return Response({"message": "Travel request updated successfully", "updated_data": serializer.data}, status=HTTP_200_OK)
    logger.error(f"Error updating travel request {request_id} - {serializer.errors}")
    return Response(serializer.errors, status=HTTP_400_BAD_REQUEST)


#Delete Travel Request
@csrf_exempt
@permission_classes([IsAuthenticated, IsEmployeeUser])
@api_view(['DELETE'])
def delete_travel_request(request, request_id):
    travel_request = get_object_or_404(Employee_Request, id=request_id)
    travel_request.delete()
    logger.info(f"Travel request {request_id} deleted by employee: {request.user.username}")
    return Response({"message": "Travel request deleted successfully"}, status=HTTP_200_OK)
    @csrf_exempt
    @api_view(['POST'])
    @permission_classes([AllowAny])
    def manager_login(request):
        """
        Authenticate a manager and return a token if credentials are valid.
        """
        if request.method == 'POST':
            data = json.loads(request.body)
            user = authenticate(username=data['username'], password=data['password'])
            if user is not None and hasattr(user, 'manager'):
                token, created = Token.objects.get_or_create(user=user)
                logger.info(f"Manager {user.username} logged in successfully.")
                return JsonResponse({'status': 'success', 'token': token.key})
            logger.warning(f"Failed login attempt for username: {data['username']}")
            return JsonResponse({'status': 'failed', 'message': 'Invalid credentials'}, status=401)
        logger.error("Invalid request method for manager_login")
        return JsonResponse({'status': 'failed', 'message': 'Invalid request method'}, status=400)

    # Manager Dashboard
    @api_view(['GET'])
    @permission_classes([IsAuthenticated, IsManagerUser])
    def manager_dashboard(request):
        manager_id = request.query_params.get("id")
        if not manager_id:
            logger.error("Manager ID is required for manager_dashboard")
            return Response({"error": "Manager ID is required"}, status=400)
        history_list = Employee_Request.objects.filter(manager_id=manager_id).select_related("employee_id")
        serializer = ManagerTableSerializer(history_list, many=True)
        logger.info(f"Manager {request.user.username} accessed their dashboard.")
        return Response(serializer.data, status=HTTP_200_OK)

    @api_view(['GET'])
    @permission_classes([IsAuthenticated, IsManagerUser])
    def filter_sort_search(request):
        manager_id = request.query_params.get("id")
        employee_name = request.query_params.get("employee_name")
        employee_id = request.query_params.get("employee_id")
        start_date = request.query_params.get("start_date")
        end_date = request.query_params.get("end_date")
        status_filter = request.query_params.get("status")
        sort_by = request.query_params.get("sort_by", "date_of_sub")

        if not manager_id:
            logger.error("Manager ID is required for filter_sort_search")
            return Response({"status": "error", "message": "Manager ID is required"}, status=status.HTTP_400_BAD_REQUEST)

        history_list = Employee_Request.objects.filter(manager=manager_id).select_related("employee")

        if employee_name:
            history_list = history_list.filter(
                Q(employee__first_name__icontains=employee_name) |
                Q(employee__last_name__icontains=employee_name)
            )
        if employee_id:
            history_list = history_list.filter(employee__id=employee_id)
        if start_date and end_date:
            history_list = history_list.filter(from_date__gte=start_date, to_date__lte=end_date)
        if status_filter:
            history_list = history_list.filter(manager_status=status_filter)

        valid_sort_fields = ["date_of_sub", "from_date", "to_date", "manager_status"]
        if sort_by in valid_sort_fields:
            history_list = history_list.order_by(sort_by)

        serializer = ManagerTableSerializer(history_list, many=True)
        logger.info(f"Manager {request.user.username} performed a filter/sort/search operation.")
        return Response(serializer.data, status=status.HTTP_200_OK)

    @api_view(["POST"])
    @permission_classes([IsAuthenticated, IsManagerUser])
    def manager_status_update(request):
        try:
            data = json.loads(request.body)
            ticket_id = data.get('ticket_id')
            manager_id = data.get('manager_id')
            manager_status = data.get('manager_status')
            feedback = data.get('feedback', '')

            try:
                ticket = Employee_Request.objects.get(id=ticket_id)
            except Employee_Request.DoesNotExist:
                logger.error(f"Ticket {ticket_id} not found for manager_status_update")
                return JsonResponse({'status': 'error', 'message': 'Ticket not found', 'data': None}, status=404)

            try:
                manager_instance = Manager.objects.get(pk=manager_id)
            except Manager.DoesNotExist:
                logger.error(f"Manager {manager_id} not found for manager_status_update")
                return JsonResponse({'status': 'error', 'message': 'Manager not found', 'data': None}, status=404)

            if ticket.manager != manager_instance:
                logger.warning(f"Unauthorized status update attempt by manager {manager_id} for ticket {ticket_id}")
                return JsonResponse({'status': 'error', 'message': 'Unauthorized: You can only manage requests assigned to you', 'data': None}, status=403)

            valid_statuses = ["Approved", "Canceled", "Pending"]
            if manager_status not in valid_statuses:
                logger.error(f"Invalid status {manager_status} provided by manager {manager_id} for ticket {ticket_id}")
                return JsonResponse({'status': 'error', 'message': 'Invalid status. Choose from Approved, Canceled, or Pending.', 'data': None}, status=400)

            ticket.manager_status = manager_status
            ticket.manager_note = feedback
            ticket.save()
            send_mail(
                'Travel Request Status Update',
                f'Your travel request with ID {ticket.id} has been updated to {manager_status}.',
                'manager@example.com',
                [ticket.employee.email],
                fail_silently=False,
            )

            logger.info(f"Manager {manager_id} updated status of ticket {ticket_id} to {manager_status}")
            return JsonResponse({'data': {'ticket_id': ticket.id, 'employee_id': ticket.employee.pk, 'manager_id': ticket.manager.pk, 'manager_status': ticket.manager_status, 'manager_note': ticket.manager_note}}, status=200)

        except json.JSONDecodeError:
            logger.error("Invalid JSON format in manager_status_update")
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON format', 'data': None}, status=400)
        
        except Exception as e:
            logger.error(f"Error in manager_status_update: {str(e)}")
            return JsonResponse({'status': 'error', 'message': str(e), 'data': None}, status=500)

@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
def admin_login(request):
    """
    Authenticate an admin and return a token if credentials are valid.
    """
    if request.method == 'POST':
        data = json.loads(request.body)
        user = authenticate(username=data['username'], password=data['password'])
        if user is not None and hasattr(user,'admin'):
            token, created = Token.objects.get_or_create(user=user)
            logger.info(f"Admin {user.username} logged in successfully.")
            return JsonResponse({'status': 'success', 'token': token.key})
        logger.warning(f"Failed login attempt for username: {data['username']}")
        return JsonResponse({'status': 'failed', 'message': 'Invalid credentials'}, status=401)
    logger.error("Invalid request method for admin_login")
    return JsonResponse({'status': 'failed', 'message': 'Invalid request method'}, status=400)


# Admin Dashboard
@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdminUser])
def admin_dashboard(request):
    history_list = Employee_Request.objects.select_related("employee", "manager").all()
    serializer = AdminTableSerializer(history_list, many=True)
    logger.info(f"Admin {request.user.username} accessed the dashboard.")
    return Response(serializer.data, status=HTTP_200_OK)


from django.contrib.auth.models import Group
# Create the 'Manager' group
Group.objects.get_or_create(name='Manager')

@api_view(["POST"])
@permission_classes([IsAdminUser])
def add_manager(request):
    try:
        data = request.data  # Use DRF's request.data instead of json.loads(request.body)
        username = data.get('username')
        first_name = data.get('first_name')
        last_name = data.get('last_name')
        email = data.get('email')
        password = data.get('password')
        date_in = data.get('date_of_joining')
        manager_active_status = data.get('manager_active_status', 'Active')

        if not all([first_name, last_name, email, password]):
            logger.error("All fields are required to add a manager.")
            return Response({'status': 'failed', 'message': 'All fields are required'}, status=400)

        if User.objects.filter(email=email).exists():
            logger.warning(f"Email {email} already registered.")
            return Response({'status': 'failed', 'message': 'Email already registered'}, status=400)

        # Creating user instance with proper password handling
        user = User.objects.create_user(username=username, email=email, password=password)
        
        # Add user to "Manager" group
        try:
            manager_group = Group.objects.get(name='Manager')
            user.groups.add(manager_group)
        except ObjectDoesNotExist:
            logger.error("Manager group does not exist.")
            return Response({'status': 'failed', 'message': 'Manager group does not exist'}, status=500)

        # Creating manager instance
        manager = Manager.objects.create(
            username=username,
            first_name=first_name,
            last_name=last_name,
            email=email,
            date_in=date_in,
            manager_active_status=manager_active_status,
            user_auth=user  # Link to Django User
        )

        logger.info(f"Manager {username} added successfully.")
        return Response({
            'status': 'success',
            'message': 'Manager added successfully',
            'data': {'first_name': first_name, 'last_name': last_name, 'email': email}
        }, status=201)

    except Exception as e:
        logger.error(f"Error adding manager: {str(e)}")
        return Response({'status': 'failed', 'message': str(e)}, status=500)


# Edit Manager
@api_view(["PUT"])
@permission_classes([IsAuthenticated, IsAdminUser])
def edit_manager(request, manager_id):
    try:
        manager = Manager.objects.get(id=manager_id)
    except Manager.DoesNotExist:
        logger.error(f"Manager {manager_id} not found.")
        return Response({'status': 'failed', 'message': 'Manager not found'}, status=status.HTTP_404_NOT_FOUND)

    # Handle updating the user_auth field if provided
    if 'email' in request.data:
        user = manager.user_auth
        user.username = request.data.get('email')
        user.save()

    serializer = ManagerSerializer(manager, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        logger.info(f"Manager {manager_id} updated successfully.")
        return Response({'status': 'success', 'message': 'Manager updated successfully', 'data': serializer.data}, status=status.HTTP_200_OK)
    logger.error(f"Error updating manager {manager_id}: {serializer.errors}")
    return Response({'status': 'failed', 'message': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

# Delete Manager
@api_view(["DELETE"])
@permission_classes([IsAuthenticated, IsAdminUser])
def delete_manager(request, manager_id):
    try:
        manager = Manager.objects.get(id=manager_id)
        user = manager.user_auth
        manager.delete()
        user.delete()  # Also delete the corresponding User instance
        logger.info(f"Manager {manager_id} deleted successfully.")
        return Response({'status': 'success', 'message': 'Manager deleted successfully'}, status=status.HTTP_200_OK)
    except Manager.DoesNotExist:
        logger.error(f"Manager {manager_id} not found.")
        return Response({'status': 'failed', 'message': 'Manager not found'}, status=status.HTTP_404_NOT_FOUND)


@api_view(["POST"])
@permission_classes([IsAdminUser])
def add_employee(request):
    try:
        data = request.data
        manager_id = data.get('manager_id')
        username = data.get('username')
        first_name = data.get('first_name')
        last_name = data.get('last_name')
        email = data.get('email')
        password = data.get('password')
        date_in = data.get('date_in')
        employee_active_status = data.get('employee_active_status', 'Active')

        if not all([username, first_name, last_name, email, password, date_in]):
            logger.error("All fields are required to add an employee.")
            return Response({'status': 'failed', 'message': 'All fields are required'}, status=400)

        try:
            date_in = datetime.strptime(date_in, "%Y-%m-%d").date()
        except ValueError:
            logger.error("Invalid date format for employee.")
            return Response({'status': 'failed', 'message': 'Invalid date format, use YYYY-MM-DD'}, status=400)

        if User.objects.filter(email=email).exists():
            logger.warning(f"Email {email} already registered.")
            return Response({'status': 'failed', 'message': 'Email already registered'}, status=400)

        user = User.objects.create_user(username=username, email=email, password=password)
        
        try:
            employee_group = Group.objects.get(name='Employee')
            user.groups.add(employee_group)
        except ObjectDoesNotExist:
            logger.error("Employee group does not exist.")
            return Response({'status': 'failed', 'message': 'Employee group does not exist'}, status=500)

        employee = Employee.objects.create(
            username=username,
            manager_id=manager_id,
            first_name=first_name,
            last_name=last_name,
            email=email,
            date_in=date_in,
            employee_active_status=employee_active_status,
            user_auth=user
        )

        logger.info(f"Employee {username} added successfully.")
        return Response({
            'status': 'success',
            'message': 'Employee added successfully',
            'data': {'first_name': first_name, 'last_name': last_name, 'email': email}
        }, status=201)

    except Exception as e:
        logger.error(f"Error adding employee: {str(e)}")
        return Response({'status': 'failed', 'message': str(e)}, status=500)

# Edit employee
@api_view(["PUT"])
@permission_classes([IsAuthenticated, IsAdminUser])
def edit_employee(request, employee_id):
    try:
        employee = Employee.objects.get(id=employee_id)
    except Employee.DoesNotExist:
        logger.error(f"Employee {employee_id} not found.")
        return Response({'status': 'failed', 'message': 'Employee not found'}, status=status.HTTP_404_NOT_FOUND)

    # Handle updating the user_auth field if provided
    if 'email' in request.data:
        user = employee.user_auth
        user.username = request.data.get('email')
        user.save()

    serializer = EmployeeSerializer(employee, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        logger.info(f"Employee {employee_id} updated successfully.")
        return Response({'status': 'success', 'message': 'Employee updated successfully', 'data': serializer.data}, status=status.HTTP_200_OK)
    logger.error(f"Error updating employee {employee_id}: {serializer.errors}")
    return Response({'status': 'failed', 'message': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

# Delete Employee
@api_view(["DELETE"])
@permission_classes([IsAuthenticated, IsAdminUser])
def delete_employee(request, employee_id):
    try:
        employee = Employee.objects.get(id=employee_id)
        user = employee.user_auth
        employee.delete()
        user.delete()  # Also delete the corresponding User instance
        logger.info(f"Employee {employee_id} deleted successfully.")
        return Response({'status': 'success', 'message': 'Employee deleted successfully'}, status=status.HTTP_200_OK)
    except Employee.DoesNotExist:
        logger.error(f"Employee {employee_id} not found.")
        return Response({'status': 'failed', 'message': 'Employee not found'}, status=status.HTTP_404_NOT_FOUND)


# Admin Status Update
@api_view(["POST"])
@permission_classes([IsAuthenticated, IsAdminUser])
def admin_status_update(request):
    try:
        data = json.loads(request.body)
        ticket_id = data.get('ticket_id')
        user_id = data.get('user_id')  # ID of the user making the request
        user_role = data.get('user_role')  # Role: "Manager" or "Admin"
        status_update = data.get('status_update')  # Approved, Canceled, Pending
        feedback = data.get('feedback', '')  # Admin note

        try:
            ticket = Employee_Request.objects.get(id=ticket_id)
        except Employee_Request.DoesNotExist:
            logger.error(f"Request {ticket_id} not found.")
            return JsonResponse({
                'status': 'error',
                'message': 'Request not found',
                'data': None
            }, status=404)

        # Validate user role and permissions
        if user_role == "Manager":
            # Managers can only modify their own requests
            if ticket.manager_id.id != int(user_id):
                logger.warning(f"Unauthorized status update attempt by manager {user_id} for ticket {ticket_id}")
                return JsonResponse({
                    'status': 'error',
                    'message': 'Unauthorized: You can only update requests assigned to you',
                    'data': None
                }, status=403)
            ticket.manager_status = status_update
            ticket.manager_note = feedback  # Add manager feedback

        elif user_role == "Admin":
            # Admins can update any request
            ticket.manager_status = status_update
            ticket.admin_note = feedback  # Admin provides feedback
        
        else:
            logger.error(f"Invalid role {user_role} provided.")
            return JsonResponse({
                'status': 'error',
                'message': 'Invalid role. Only "Manager" or "Admin" allowed.',
                'data': None
            }, status=403)

        # Validate status input
        valid_statuses = ["Approved", "Canceled", "Pending"]
        if status_update not in valid_statuses:
            logger.error(f"Invalid status {status_update} provided.")
            return JsonResponse({
                'status': 'error',
                'message': 'Invalid status. Choose from Approved, Canceled, or Pending.',
                'data': None
            }, status=400)

        ticket.save()
        send_mail(
            'Travel Request Status Update',
            f'Your travel request with ID {ticket.id} has been updated to {status_update}.',
            'indulekshmi@example.com',
            [ticket.employee.email],
            fail_silently=False,
        )
        logger.info(f"Status of ticket {ticket_id} updated to {status_update} by {user_role} {user_id}")

        return JsonResponse({
            'data': {
                'ticket_id': ticket.id,
                'employee_id': ticket.employee_id.id,
                'manager_id': ticket.manager_id.id,
                'manager_status': ticket.manager_status,
                'manager_note': ticket.manager_note,
                'admin_note': ticket.admin_note,  # Include admin note if updated
            }
        }, status=200)

    except json.JSONDecodeError:
        logger.error("Invalid JSON format in admin_status_update")
        return JsonResponse({
            'status': 'error',
            'message': 'Invalid JSON format',
            'data': None
        }, status=400)
    
    except Exception as e:
        logger.error(f"Error in admin_status_update: {str(e)}")
        return JsonResponse({
            'status': 'error',
            'message': str(e),
            'data': None
        }, status=500)

# Close Ticket
@api_view(["POST"])
@permission_classes([IsAuthenticated, IsAdminUser])
def close_ticket(request):
    try:
        data = json.loads(request.body)
        ticket_id = data.get('ticket_id')

        # Ensure ticket exists
        try:
            ticket = Employee_Request.objects.get(id=ticket_id)
        except Employee_Request.DoesNotExist:
            logger.error(f"Ticket {ticket_id} not found.")
            return JsonResponse({
                'status': 'error',
                'message': 'Ticket not found',
                'data': None
            }, status=404)

        # Check if the request is approved by the manager before closing
        if ticket.manager_status != "Approved":
            logger.warning(f"Attempt to close unapproved ticket {ticket_id}")
            return JsonResponse({
                'status': 'error',
                'message': 'Only approved requests can be closed',
                'data': {
                    'ticket_id': ticket.id,
                    'manager_status': ticket.manager_status,
                    'admin_status': ticket.admin_status
                }
            }, status=400)

        # Update ticket status
        ticket.admin_status = "Closed"
        ticket.save()
        logger.info(f"Ticket {ticket_id} closed successfully.")
        send_mail(
            'Travel Request Closed',
            f'Your travel request with ID {ticket.id} has been closed.',
            'inudlekshmi@example.com',
            [ticket.employee.email],            
            fail_silently=False,
        )

        return JsonResponse({
            'status': 'success',
            'message': 'Ticket closed successfully',
            'data': {
                'ticket_id': ticket.id,
                'employee_id': ticket.employee_id.id,
                'manager_id': ticket.manager_id.id,
                'manager_status': ticket.manager_status,
                'admin_status': ticket.admin_status,
                'admin_note': ticket.admin_note
            }
        }, status=200)
    
    except json.JSONDecodeError:
        logger.error("Invalid JSON format in close_ticket")
        return JsonResponse({
            'status': 'error',
            'message': 'Invalid JSON format',
            'data': None
        }, status=400)
    
    except Exception as e:
        logger.error(f"Error in close_ticket: {str(e)}")
        return JsonResponse({
            'status': 'error',
            'message': str(e),
            'data': None
        }, status=500)


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdminUser])
def list_employees(request):
    employees = Employee.objects.all().values('id', 'first_name', 'last_name', 'email')
    logger.info("Admin accessed the list of employees.")
    return Response({"employees": list(employees)})

@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdminUser])
def list_managers(request):
    managers = Manager.objects.all().values('id', 'first_name', 'last_name', 'email')
    logger.info("Admin accessed the list of managers.")
    return Response({"managers": list(managers)})

@csrf_exempt
@api_view(["POST"])
@permission_classes([AllowAny])
def add_admin(request):
    """
    Add a new admin user.
    """
    try:
        data = json.loads(request.body)
        username = data.get('username')
        password = data.get('password') 
        first_name = data.get('first_name')
        last_name = data.get('last_name')
        email = data.get('email')
        date_in = data.get('date_in')  
        if not all([username, password]):
            logger.error("All fields are required to add an admin.")
            return JsonResponse({
                'status': 'failed', 
                'message': 'All fields are required'
            }, status=400)
        user = User.objects.create_user(
            username=username,
            password=password,
        )
        admin = Admin.objects.create(
            username=username,
            password=password,
            first_name=first_name,
            last_name=last_name,
            email=email,
            date_in=date_in,
            user_auth=user
        ) 
        admin.save()
        logger.info(f"Admin {username} added successfully.")       
        return JsonResponse({
            'status': 'success', 
            'data': {
                'username': username, 
            }
        })
    except json.JSONDecodeError:
        logger.error("Invalid JSON format in add_admin")
        return JsonResponse({
            'status': 'failed', 
            'message': 'Invalid JSON format'
        }, status=400)
    except Exception as e:
        logger.error(f"Error adding admin: {str(e)}")
        return JsonResponse({
            'status': 'failed', 
            'message': str(e)
        }, status=500)