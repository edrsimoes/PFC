from django.contrib import admin

from .models import (
    Achievement, CareerHistory, DecisionEvent, DecisionLog, DecisionOption,
    News, PlayerAchievement, Season, Training,
)


@admin.register(Season)
class SeasonAdmin(admin.ModelAdmin):
    list_display = ("jogador", "ano", "clube", "jogos", "gols", "assistencias", "encerrada")
    list_filter = ("ano", "encerrada")


@admin.register(Training)
class TrainingAdmin(admin.ModelAdmin):
    list_display = ("jogador", "tipo", "energia_consumida", "realizado_em")
    list_filter = ("tipo",)


@admin.register(Achievement)
class AchievementAdmin(admin.ModelAdmin):
    list_display = ("codigo", "titulo", "icone")


@admin.register(PlayerAchievement)
class PlayerAchievementAdmin(admin.ModelAdmin):
    list_display = ("jogador", "achievement", "desbloqueada_em")


@admin.register(CareerHistory)
class CareerHistoryAdmin(admin.ModelAdmin):
    list_display = ("jogador", "ano", "titulo", "clube")


@admin.register(News)
class NewsAdmin(admin.ModelAdmin):
    list_display = ("titulo", "jogador", "categoria", "publicada_em")
    list_filter = ("categoria",)


class DecisionOptionInline(admin.TabularInline):
    model = DecisionOption
    extra = 1


@admin.register(DecisionEvent)
class DecisionEventAdmin(admin.ModelAdmin):
    list_display = ("titulo", "codigo", "contexto")
    inlines = [DecisionOptionInline]


@admin.register(DecisionLog)
class DecisionLogAdmin(admin.ModelAdmin):
    list_display = ("jogador", "evento", "opcao_escolhida", "decidido_em")
