from django.shortcuts import render,get_object_or_404
from django.contrib.auth import authenticate
from rest_framework.decorators import api_view,permission_classes
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND,HTTP_401_UNAUTHORIZED, HTTP_500_INTERNAL_SERVER_ERROR
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
from django.core.exceptions import ObjectDoesNotExist

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

@csrf_exempt
@api_view(['POST'])
@permission_classes([IsAuthenticated, IsEmployeeUser])
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

# Edit Travel Request
@api_view(['PUT'])
@permission_classes([IsAuthenticated, IsEmployeeUser])
def edit_travel_request(request, request_id):
    try:
        user = request.user
        # Validate Employee
        employee = Employee.objects.filter(user_auth=user).first()
        if not employee:
            logger.error(f"Invalid Employee for user: {user.username}")
            return Response({"status": "failed", "message": "Invalid Employee"}, status=status.HTTP_404_NOT_FOUND)

        # Validate Travel Request
        travel_request = Employee_Request.objects.filter(id=request_id, employee=employee).first()
        if not travel_request:
            logger.error(f"Travel request {request_id} not found for employee: {user.username}")
            return Response({"status": "failed", "message": "Travel request not found"}, status=status.HTTP_404_NOT_FOUND)

        # Update Travel Request
        data = request.data
        serializer = EmployeeTableSerializer(travel_request, data=data, partial=True)
        if serializer.is_valid():
            serializer.save()
            logger.info(f"Travel request {request_id} updated by employee: {user.username}")
            return Response({"status": "success", "message": "Travel request updated successfully", "updated_data": serializer.data}, status=HTTP_200_OK)
        logger.error(f"Error updating travel request {request_id} - {serializer.errors}")
        return Response({"status": "failed", "message": serializer.errors}, status=HTTP_400_BAD_REQUEST)

    except Exception as e:
        logger.error(f"Error updating travel request {request_id} for employee: {user.username} - {str(e)}")
        return Response({"status": "failed", "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)


# Delete Travel Request
@api_view(['DELETE'])
@permission_classes([IsAuthenticated, IsEmployeeUser])
def delete_travel_request(request, request_id):
    try:
        user = request.user
        # Validate Employee
        employee = Employee.objects.filter(user_auth=user).first()
        if not employee:
            logger.error(f"Invalid Employee for user: {user.username}")
            return Response({"status": "failed", "message": "Invalid Employee"}, status=status.HTTP_404_NOT_FOUND)

        # Validate Travel Request
        travel_request = Employee_Request.objects.filter(id=request_id, employee=employee).first()
        if not travel_request:
            logger.error(f"Travel request {request_id} not found for employee: {user.username}")
            return Response({"status": "failed", "message": "Travel request not found"}, status=status.HTTP_404_NOT_FOUND)

        # Delete Travel Request
        travel_request.delete()
        logger.info(f"Travel request {request_id} deleted by employee: {user.username}")
        return Response({"status": "success", "message": "Travel request deleted successfully"}, status=HTTP_200_OK)

    except Exception as e:
        logger.error(f"Error deleting travel request {request_id} for employee: {user.username} - {str(e)}")
        return Response({"status": "failed", "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        
@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
def manager_login(request):
    """
    Authenticate an admin and return a token if credentials are valid.
    """
    if request.method == 'POST':
        data = json.loads(request.body)
        user = authenticate(username=data['username'], password=data['password'])
        if user is not None and hasattr(user,'manager'):
            token, created = Token.objects.get_or_create(user=user)
            return JsonResponse({'status': 'success', 'token': token.key})
        return JsonResponse({'status': 'failed', 'message': 'Invalid credentials'}, status=401)
    return JsonResponse({'status': 'failed', 'message': 'Invalid request method'}, status=400)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def manager_dashboard(request):
    try:
        # Fetch the Manager instance linked to the authenticated user
        manager = Manager.objects.get(user_auth=request.user)

        # Get all employees under this manager
        employees = Employee.objects.filter(manager=manager)

        # If no employees are assigned to this manager, return an empty list
        if not employees.exists():
            logger.info(f"Manager {request.user.username} has no employees assigned.")
            return Response([], status=HTTP_200_OK)  # ✅ Return an empty list

        # Get all travel requests assigned to these employees
        history_list = Employee_Request.objects.filter(employee__in=employees).select_related("employee")

        # If no requests exist, return an empty list
        if not history_list.exists():
            logger.info(f"Manager {request.user.username} has no assigned travel requests.")
            return Response([], status=HTTP_200_OK)  # ✅ Return an empty list

        # Serialize the data
        serializer = ManagerTableSerializer(history_list, many=True)

        logger.info(f"Manager {request.user.username} accessed their dashboard successfully.")
        return Response(serializer.data, status=HTTP_200_OK)  # ✅ Return data directly

    except Manager.DoesNotExist:
        logger.error(f"Manager record not found for user {request.user.username}")
        return Response({'error': 'Manager record not found'}, status=HTTP_404_NOT_FOUND)

    except Exception as e:
        logger.error(f"Error accessing manager dashboard: {str(e)}")
        return Response({'error': str(e)}, status=HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def filter_sort_search(request):
    """Filters and sorts Employee Requests based on query parameters"""
    
    # Get filter parameters from request
    first_name = request.query_params.get("first_name", "").strip()
    last_name = request.query_params.get("last_name", "").strip()
    employee_id = request.query_params.get("employee_id", "").strip()
    start_date = request.query_params.get("start_date", "").strip()
    end_date = request.query_params.get("end_date", "").strip()
    manager_status = request.query_params.get("manager_status", "").strip()
    admin_status = request.query_params.get("admin_status", "").strip()
    sort_field = request.query_params.get("sort_field", "date_of_sub").strip()
    sort_order = request.query_params.get("sort_order", "asc").strip()

    # Start with all records
    queryset = Employee_Request.objects.all()

    # Apply filters
    if first_name:
        queryset = queryset.filter(employee__first_name__icontains=first_name)
    if last_name:
        queryset = queryset.filter(employee__last_name__icontains=last_name)
    if employee_id:
        queryset = queryset.filter(employee__id=employee_id)
    if start_date:
        queryset = queryset.filter(from_date__gte=start_date)
    if end_date:
        queryset = queryset.filter(to_date__lte=end_date)
    if manager_status:
        queryset = queryset.filter(manager_status=manager_status)
    if admin_status:
        queryset = queryset.filter(admin_status=admin_status)

    # Sorting logic
    if sort_field in ["date_of_sub", "from_date", "to_date", "first_name", "last_name"]:
        if sort_order == "desc":
            sort_field = f"-{sort_field}"
        queryset = queryset.order_by(sort_field)

    # Serialize and return filtered/sorted data
    serializer = EmployeeTableSerializer(queryset, many=True)
    return Response(serializer.data)

@api_view(["PUT"])
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

        valid_statuses = ["Approved", "Declined", "Pending", "OnProgress"]
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


@api_view(['POST'])
@permission_classes([AllowAny])
def admin_login(request):
    """
    Authenticate an admin and return a token if credentials are valid.
    """
    if request.method == 'POST':
        data = request.data  # DRF automatically parses JSON

        user = authenticate(username=data.get('username'), password=data.get('password'))

        if user is not None:
            try:
                # Check if user exists in Admin model and has is_admin=True
                admin_user = Admin.objects.get(user_auth=user, is_admin=True)

                # Generate or get authentication token
                token, created = Token.objects.get_or_create(user=user)
                logger.info(f"Admin {user.username} logged in successfully.")

                return Response({
                    'status': 'success',
                    'token': token.key
                }, status=200)

            except Admin.DoesNotExist:
                return Response({'status': 'failed', 'message': 'User is not an admin'}, status=403)

        logger.warning(f"Failed login attempt for username: {data.get('username')}")
        return Response({'status': 'failed', 'message': 'Invalid credentials'}, status=401)

    logger.error("Invalid request method for admin_login")
    return Response({'status': 'failed', 'message': 'Invalid request method'}, status=400)

# Admin Dashboard
@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdminUser])
def admin_dashboard(request):
    history_list = Employee_Request.objects.select_related("employee", "manager").all()
    serializer = AdminTableSerializer(history_list, many=True)
    logger.info(f"Admin {request.user.username} accessed the dashboard.")
    return Response(serializer.data, status=HTTP_200_OK)



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
@permission_classes([IsAdminUser])
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
@permission_classes([IsAdminUser])
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
@permission_classes([IsAdminUser])
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
@permission_classes([IsAdminUser])
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
@permission_classes([IsAdminUser])
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
@permission_classes([IsAdminUser])
def close_ticket(request):
    try:
        data = json.loads(request.body)
        ticket_id = data.get("ticket_id")
        admin_note = data.get("admin_note", "").strip()

        # Ensure ticket exists
        try:
            ticket = Employee_Request.objects.get(id=ticket_id)
        except Employee_Request.DoesNotExist:
            logger.error(f"Ticket {ticket_id} not found.")
            return JsonResponse({
                "status": "error",
                "message": "Ticket not found",
                "data": None
            }, status=404)

        # Admin can only close requests that are approved by the manager
        if ticket.manager_status != "Approved":
            return JsonResponse({
                "status": "error",
                "message": "Only approved requests can be closed",
                "data": {
                    "ticket_id": ticket.id,
                    "manager_status": ticket.manager_status,
                    "admin_status": ticket.admin_status
                }
            }, status=400)

        # If admin_status is already "Closed", allow updating the admin note
        if ticket.admin_status == "Closed":
            if not admin_note:
                return JsonResponse({
                    "status": "error",
                    "message": "Admin note is required for closed tickets",
                    "data": None
                }, status=400)
            ticket.admin_note = admin_note
            ticket.save()
            return JsonResponse({
                "status": "success",
                "message": "Admin note updated for closed ticket",
                "data": {
                    "ticket_id": ticket.id,
                    "admin_status": ticket.admin_status,
                    "admin_note": ticket.admin_note
                }
            }, status=200)

        # Otherwise, close the ticket
        ticket.admin_status = "Closed"
        ticket.admin_note = admin_note if admin_note else "No additional notes."
        ticket.save()
        
        # Send email notification
        send_mail(
            "Travel Request Closed",
            f"Your travel request with ID {ticket.id} has been closed. Note: {ticket.admin_note}",
            "admin@example.com",
            [ticket.employee.email],            
            fail_silently=False,
        )

        return JsonResponse({
            "status": "success",
            "message": "Ticket closed successfully",
            "data": {
                "ticket_id": ticket.id,
                "employee_id": ticket.employee.id,
                "manager_id": ticket.manager.id,
                "manager_status": ticket.manager_status,
                "admin_status": ticket.admin_status,
                "admin_note": ticket.admin_note
            }
        }, status=200)

    except json.JSONDecodeError:
        return JsonResponse({
            "status": "error",
            "message": "Invalid JSON format",
            "data": None
        }, status=400)

    except Exception as e:
        logger.error(f"Error in close_ticket: {str(e)}")
        return JsonResponse({
            "status": "error",
            "message": str(e),
            "data": None
        }, status=500)



@api_view(['GET'])
@permission_classes([IsAdminUser])
def list_employees(request):
    employees = Employee.objects.all().values('id', 'first_name', 'last_name', 'email')
    logger.info("Admin accessed the list of employees.")
    return Response({"employees": list(employees)})

@api_view(['GET'])
@permission_classes([IsAdminUser])
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

@csrf_exempt
@api_view(['POST'])
def user_logout(request):
    logger.info("User logout requested")
    """
    Log out the user and delete their authentication token.
    """
    if request.method == 'POST':
        request.user.auth_token.delete()
        logout(request)
        logger.info("User logged out successfully")
        return JsonResponse({'status': 'success', 'message': 'Logged out successfully'})
    logger.warning("Invalid request method for user logout")
    return JsonResponse({'status': 'failed', 'message': 'Invalid request method'}, status=400)        