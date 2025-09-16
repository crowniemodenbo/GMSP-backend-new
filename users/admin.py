
# Register your models here.
# admin.py
from django.contrib import admin
from .models import User, Pairing
from django.utils.translation import gettext_lazy as _
from .models import Pairing, User

class MentorFullNameFilter(admin.SimpleListFilter):
    title = _('Mentor')
    parameter_name = 'mentor'

    def lookups(self, request, model_admin):
        return [(u.id, u.full_name) for u in User.objects.filter(role='mentor')]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(mentor__id=self.value())
        return queryset


class StudentFullNameFilter(admin.SimpleListFilter):
    title = _('Student')
    parameter_name = 'student'

    def lookups(self, request, model_admin):
        return [(u.id, u.full_name) for u in User.objects.filter(role='student')]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(student__id=self.value())
        return queryset

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('email', 'first_name', 'last_name', 'role', 'is_active')
    list_filter = ('role', 'is_active')
    search_fields = ('email', 'first_name', 'last_name')

@admin.register(Pairing)
class PairingAdmin(admin.ModelAdmin):
    list_display = ('mentor', 'student')
    search_fields = ('mentor__email', 'student__email','mentor__first_name', 'student__first_name', 'mentor__last_name', 'student__last_name')
    list_filter = (MentorFullNameFilter, StudentFullNameFilter)

