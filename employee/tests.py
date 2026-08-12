from django.test import TestCase

from sozlamalar.models import Branch
from employee.models import Employee, User, Role
from employee.serializer import EmployeeCreateSerializer, EmployeeSerializer


class EmployeeBranchAssignmentTests(TestCase):
    def test_employee_serializer_includes_branch_data(self):
        branch = Branch.objects.create(name="Farg'ona", city="Farg'ona")
        role, _ = Role.objects.get_or_create(name="manager_branch_serializer", defaults={"label": "Boshliq"})
        user, _ = User.objects.get_or_create(phone="+998901234567")
        employee = Employee.objects.create(
            user=user,
            first_name="Ali",
            last_name="Valiyev",
            role=role,
            branch=branch,
        )

        data = EmployeeSerializer(employee).data

        self.assertEqual(data["branch"]["id"], branch.id)
        self.assertEqual(data["branch"]["name"], "Farg'ona")

    def test_employee_create_serializer_accepts_branch_id(self):
        branch = Branch.objects.create(name="Andijon", city="Andijon")
        role, _ = Role.objects.get_or_create(name="manager_branch_create", defaults={"label": "Boshliq"})

        payload = {
            "first_name": "Bobur",
            "last_name": "Nazarov",
            "phone": "+998901234568",
            "password": "1234",
            "role_id": role.id,
            "branch_id": branch.id,
        }

        serializer = EmployeeCreateSerializer(data=payload)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        employee = serializer.save()

        self.assertEqual(employee.branch_id, branch.id)
