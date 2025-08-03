from django.contrib import admin
from .models import Peak, Picture


class PicturesInline(admin.TabularInline):
    model = Picture
    extra = 0

class PeakAdmin(admin.ModelAdmin):
    inlines = [
        PicturesInline,
    ]

admin.site.register(Peak, PeakAdmin)
admin.site.register(Picture)