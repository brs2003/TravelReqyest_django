from django.db import models
from datetime import date
from django.contrib.auth.models import User

# Create your models here.
status = (
    ("Active", "Active"),
    ("Inactive", "Inactive")
)

class Employee(models.Model):
    username = models.CharField(max_length=150, unique=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100, null=False)
    manager = models.ForeignKey("Manager", on_delete=models.PROTECT)
    Gender = models.CharField(max_length=10)
    Place = models.CharField(max_length=100)
    email = models.CharField(max_length=50, unique=True)
    password = models.CharField(max_length=20)
    date_in = models.DateField(default=date.today)
    employee_active_status = models.CharField(max_length=20, choices=status, default="Active")
    user_auth = models.OneToOneField(User, on_delete=models.CASCADE, null=True)

class Admin(models.Model):
    username = models.CharField(max_length=150, unique=True)
    date_in = models.DateField(default=date.today)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100, null=False)
    email = models.CharField(max_length=50, unique=True)
    password = models.CharField(max_length=20)
    user_auth = models.OneToOneField(User, on_delete=models.CASCADE, null=True)

class Manager(models.Model):
    username = models.CharField(max_length=150, unique=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100, null=False)
    email = models.CharField(max_length=50, unique=True)
    password = models.CharField(max_length=20)
    date_in = models.DateField(default=date.today)
    manager_active_status = models.CharField(max_length=20, choices=status, default="Active")
    user_auth = models.OneToOneField(User, on_delete=models.CASCADE, null=True)

lodging = (
    ("Yes", "Yes"),
    ("No", "No")
)

travel_mode = (
    ("Flight", "Flight"),
    ("Train", "Train"),
    ("Bus", "Bus"),
    ("Car", "Car")
)

admin_closing_status = (
    ("Closed", "Closed"),
    ("Not_Closed", "Not_closed")
)

manager_approval_status = (
    ("Approved", "Approved"),
    ("Declined", "Declined"),
    ("Pending", "Pending")
)

class Employee_Request(models.Model):
    employee = models.ForeignKey("Employee", on_delete=models.PROTECT)
    manager = models.ForeignKey("Manager", on_delete=models.PROTECT)
    date_of_sub = models.DateField(default=date.today)
    purpose = models.CharField(max_length=100)
    from_loc = models.CharField(max_length=100)
    to_loc = models.CharField(max_length=100)
    travel_mode = models.CharField(max_length=20, choices=travel_mode)
    from_date = models.DateField()
    to_date = models.DateField()
    lodging_required = models.CharField(max_length=20, choices=lodging, default="No")
    additional_request = models.CharField(max_length=300)
    manager_note = models.CharField(max_length=300)
    manager_note = models.CharField(max_length=300)
    admin_note = models.CharField(max_length=300)
    no_of_resub = models.IntegerField()
    manager_status = models.CharField(max_length=20,choices=manager_approval_status,default="Pending")
    admin_status = models.CharField(max_length=20,choices=admin_closing_status,default="Not_closed")




    
        



