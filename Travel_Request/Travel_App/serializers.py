
from rest_framework import serializers
from .models import Employee_Request,Employee,Manager,Admin


class TicketRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = Employee_Request
        fields = ['__all__']


class EmployeeTableSerializer(serializers.ModelSerializer):
    class Meta:
        model = Employee_Request        
        fields = ['employee_id','from_date','to_date','purpose','manager_note','admin_note','manager_status']

class EmployeeNameSerializer(serializers.ModelSerializer):
    class Meta:
        model = Employee
        fields = ["id", "first_name","last_name"]        

class ManagerTableSerializer(serializers.ModelSerializer):
    employee = EmployeeNameSerializer(read_only=True)  
    req_id = serializers.IntegerField(source="id")

    class Meta:
        model = Employee_Request
        fields = [
            "req_id",
            "employee",
            "from_date",
            "to_date",
            "purpose",
            "manager_status",
        ]     
        


class ManagerNameSerializer(serializers.ModelSerializer):
    """Serializer to return manager name details"""
    class Meta:
        model = Manager
        fields = ["id", "first_name", "last_name", "email"]

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
            "manager_status"
        ]

class ManagerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Manager
        fields = '__all__'

class EmployeeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Employee
        fields = '__all__'        












