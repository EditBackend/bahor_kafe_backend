from django.contrib.auth import get_user_model
from django.db import transaction
from drf_yasg.utils import swagger_auto_schema
from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from rest_framework.generics import RetrieveUpdateAPIView
from django.contrib.auth.models import update_last_login
from .models import EmployeePermission, Employee, AppModules, Role, RoleModulePermission, SalaryRecord
from .serializer import (
    EmployeePermissionSerializer,
    EmployeeSerializer,
    EmployeeCreateSerializer,
    LoginSerializer,
    PinSetSerializer,
    PinLoginSerializer,
    MeSerializer,
    RoleSerializer,
    RoleModulePermissionSerializer,
    SalaryRecordSerializer,
)

class AppModuleListView(APIView):
    def get(self, request):
        data = [{"key": choice[0], "name": choice[1]} for choice in AppModules.choices]
        return Response(data)


class RoleViewSet(viewsets.ModelViewSet):
    queryset = Role.objects.all().order_by('name')
    serializer_class = RoleSerializer
    permission_classes = []


class RoleModulePermissionViewSet(viewsets.ModelViewSet):
    queryset = RoleModulePermission.objects.select_related('role').all()
    serializer_class = RoleModulePermissionSerializer
    permission_classes = []

    def get_queryset(self):
        queryset = super().get_queryset()
        role_id = self.request.query_params.get('role')
        if role_id:
            queryset = queryset.filter(role_id=role_id)
        return queryset


class SalaryRecordViewSet(viewsets.ModelViewSet):
    queryset = SalaryRecord.objects.select_related('employee', 'employee__user').all().order_by('-created_at')
    serializer_class = SalaryRecordSerializer
    permission_classes = []

    def get_queryset(self):
        queryset = super().get_queryset()
        employee_id = self.request.query_params.get('employee')
        if employee_id:
            queryset = queryset.filter(employee_id=employee_id)
        status_param = self.request.query_params.get('status')
        if status_param:
            queryset = queryset.filter(status=status_param)
        salary_type = self.request.query_params.get('salary_type')
        if salary_type:
            queryset = queryset.filter(salary_type=salary_type)
        return queryset


User = get_user_model()
class EmployeeViewSet(viewsets.ModelViewSet):
    # permission_classes = [IsAuthenticated]
    def get_queryset(self):
        queryset = (
            Employee.objects
            .select_related("user")
            .all()
            .order_by("name")
        )
        role = self.request.query_params.get("role")
        is_active = self.request.query_params.get("is_active")
        search = self.request.query_params.get("search")
        if role:
            if role.isdigit():
                queryset = queryset.filter(role_id=role)
            else:
                queryset = queryset.filter(role__name=role)
        if is_active is not None:
            if is_active.lower() == "true":
                queryset = queryset.filter(is_active=True)
            elif is_active.lower() == "false":
                queryset = queryset.filter(is_active=False)
        if search:
            queryset = queryset.filter(name__icontains=search.strip())
        return queryset
    def get_serializer_class(self):
        if self.action == "create":
            return EmployeeCreateSerializer
        return EmployeeSerializer
    @transaction.atomic
    def perform_create(self, serializer):
        serializer.save()
    @transaction.atomic
    def perform_update(self, serializer):
        serializer.save()
    def destroy(self, request, *skip_args, **kwargs):
        instance = self.get_object()
        instance.is_active = False
        instance.save()
        return Response(
            {"message": "Xodim muvaffaqiyatli o'chirildi (nofaol holatga o'tkazildi)."},
            status=status.HTTP_200_OK
        )


class LoginAPIView(APIView):
    permission_classes = []
    @swagger_auto_schema(request_body=LoginSerializer, responses={200: LoginSerializer})
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        employee = serializer.validated_data["employee"]
        update_last_login(None, user)
        token, _ = Token.objects.get_or_create(user=user)
        return Response({
            "token": token.key,
            "employee": MeSerializer(employee).data,
            "message": "Muvaffaqiyatli login qilindi."
        }, status=status.HTTP_200_OK)


class SetPinAPIView(APIView):
    # permission_classes = [IsAuthenticated]
    @swagger_auto_schema(request_body=PinSetSerializer, responses={200: PinSetSerializer})
    def post(self, request):
        serializer = PinSetSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            employee = request.user.employee
        except Employee.DoesNotExist:
            return Response(
                {"detail": "Xodim profili topilmadi."},
                status=status.HTTP_404_NOT_FOUND
            )
        employee.quick_pin = serializer.validated_data["quick_pin"]
        employee.pin_is_set = True
        employee.save(update_fields=["quick_pin", "pin_is_set", "updated_at"])
        return Response({
            "message": "PIN muvaffaqiyatli o‘rnatildi."
        }, status=status.HTTP_200_OK)


class PinLoginAPIView(APIView):
    permission_classes = []
    @swagger_auto_schema(request_body=PinLoginSerializer, responses={200: PinLoginSerializer})
    def post(self, request):
        serializer = PinLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        employee = serializer.validated_data["employee"]
        update_last_login(None, user)
        token, _ = Token.objects.get_or_create(user=user)
        return Response({
            "token": token.key,
            "employee": MeSerializer(employee).data,
            "message": "PIN orqali muvaffaqiyatli login qilindi."
        }, status=status.HTTP_200_OK)


class MeAPIView(APIView):
    # permission_classes = [IsAuthenticated]
    def get(self, request):
        if not request.user or request.user.is_anonymous:
            return Response({"detail": "Avtorizatsiyadan o'tilmagan."}, status=status.HTTP_401_UNAUTHORIZED)
        try:
            employee = request.user.employee
        except Exception:
            return Response(
                {"detail": "Ushbu foydalanuvchiga biriktirilgan xodim profili topilmadi. Admin paneldan xodimni User-ga bog'lang."},
                status=status.HTTP_404_NOT_FOUND
            )
        try:
            serializer = MeSerializer(employee)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {"detail": f"Serializerda xatolik yuz berdi: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST
            )
class LogoutAPIView(APIView):
    # permission_classes = [IsAuthenticated]
    def post(self, request):
        request.auth.delete()
        return Response({"message": "Logout qilindi."}, status=status.HTTP_200_OK)


class EmployeePermissionAPIView(APIView):
    permission_classes = []
    def get(self, request):
        employee_id = request.query_params.get("employee")
        if not employee_id:
            return Response(
                {"error": "employee (xodim ID si) query parametri yuborilishi shart."},
                status=status.HTTP_400_BAD_REQUEST
            )
        try:
            employee = Employee.objects.get(id=employee_id)
        except Employee.DoesNotExist:
            return Response({"error": "Xodim topilmadi."}, status=status.HTTP_404_NOT_FOUND)
        perm, created = EmployeePermission.objects.get_or_create(
            employee=employee,
            defaults={
                "can_payment": False,
                "can_discount": False,
                "can_cancel_order": False,
                "can_income": False
            }
        )
        data = {
            "employee": employee.id,
            "can_payment": perm.can_payment,
            "can_discount": perm.can_discount,
            "can_cancel_order": perm.can_cancel_order,
            "can_income": perm.can_income
        }
        return Response(data, status=status.HTTP_200_OK)
    def post(self, request):
        employee_id = request.data.get("employee")
        if not employee_id:
            return Response(
                {"error": "employee ID (xodim ID si) yuborilishi shart."},
                status=status.HTTP_400_BAD_REQUEST
            )
        obj, created = EmployeePermission.objects.update_or_create(
            employee_id=employee_id,
            defaults={
                "can_payment": request.data.get("can_payment", False),
                "can_discount": request.data.get("can_discount", False),
                "can_cancel_order": request.data.get("can_cancel_order", False),
                "can_income": request.data.get("can_income", False),
            }
        )
        return Response(
            {"message": "Barcha ruxsatnomalar muvaffaqiyatli saqlandi!"},
            status=status.HTTP_200_OK
        )