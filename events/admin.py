from django.contrib import admin
from .models import EventCategory

admin.site.register(EventCategory)

from .models import Event

admin.site.register(Event)
from .models import EventMember

admin.site.register(EventMember)

from .models import SupportRequest


@admin.register(SupportRequest)
class SupportRequestAdmin(admin.ModelAdmin):

    list_display = (
        'name',
        'email',
        'subject',
        'status',
        'created_at'
    )

    list_filter = ('status',)