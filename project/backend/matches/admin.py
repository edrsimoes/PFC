from django.contrib import admin

from .models import Match, MatchEvent


class MatchEventInline(admin.TabularInline):
    model = MatchEvent
    extra = 0


@admin.register(Match)
class MatchAdmin(admin.ModelAdmin):
    list_display = ("jogador", "adversario", "gols_time", "gols_adversario", "gols_jogador", "nota_jogador")
    list_filter = ("importancia", "mandante")
    inlines = [MatchEventInline]


@admin.register(MatchEvent)
class MatchEventAdmin(admin.ModelAdmin):
    list_display = ("partida", "minuto", "tipo", "descricao")
