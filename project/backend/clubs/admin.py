from django.contrib import admin

from .models import Club, Competition, League


@admin.register(League)
class LeagueAdmin(admin.ModelAdmin):
    list_display = ("nome", "pais", "nivel", "prestigio")
    search_fields = ("nome", "pais")


@admin.register(Competition)
class CompetitionAdmin(admin.ModelAdmin):
    list_display = ("nome", "tipo", "continente", "prestigio")
    list_filter = ("tipo",)


@admin.register(Club)
class ClubAdmin(admin.ModelAdmin):
    list_display = ("nome", "pais", "liga", "overall_minimo", "prestigio")
    list_filter = ("pais", "liga")
    search_fields = ("nome",)
