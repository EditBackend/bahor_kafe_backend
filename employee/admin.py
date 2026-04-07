from django.contrib import admin
from django.contrib.auth.models import User
from employee.models import Employee, EmployeePermission

admin.site.register(User)
admin.site.register(Employee)
admin.site.register(EmployeePermission)