
from rest_framework import serializers
from .models import Employee_Request,Employee,Manager,Admin


class TicketRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = Employee_Request
        fields = ['__all__']




class EmployeeNameSerializer(serializers.ModelSerializer):
    class Meta:
        model = Employee
        fields = ["id", "first_name","last_name"]        

class ManagerTableSerializer(serializers.ModelSerializer):
    employee = EmployeeNameSerializer(read_only=True)  
    req_id = serializers.IntegerField(source="id",read_only=True)

    class Meta:
        model = Employee_Request
        fields = [
            "req_id",
            "employee",
            "from_date",
            "to_date",
            "purpose",
            "manager_status",
            "from_loc",
            "to_loc",
            "travel_mode",
            "lodging_required",
            "additional_request",
            "manager_note",
            "admin_note",
            "admin_status",
            
        ]     
        


class ManagerNameSerializer(serializers.ModelSerializer):
    """Serializer to return manager name details"""
    class Meta:
        model = Manager
        fields = ["id", "first_name", "last_name", "email"]

class EmployeeTableSerializer(serializers.ModelSerializer):
    manager=ManagerNameSerializer(read_only=True)  # Nested Manager Data
    class Meta:
        model = Employee_Request        
        fields = ['id','employee_id','from_date','to_date','purpose','manager_note','admin_note','manager_status','manager','from_loc','to_loc','travel_mode','lodging_required','additional_request','admin_status']

class AdminTableSerializer(serializers.ModelSerializer):
    employee = EmployeeNameSerializer(read_only=True)  # Nested Employee Data
    manager = ManagerNameSerializer(read_only=True)    # Nested Manager Data
    req_id = serializers.IntegerField(source="id", read_only=True)

    class Meta:
        model = Employee_Request
        fields = [
            "req_id",
            "employee",
            "manager",
            "from_date",
            "to_date",
            "purpose",
            "manager_status",
            "from_loc",
            "to_loc",
            "travel_mode",
            "lodging_required",
            "additional_request",
            "admin_note",
            "admin_status",
            "no_of_resub"
        ]

class ManagerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Manager
        fields = '__all__'

class EmployeeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Employee
        fields = '__all__'        













