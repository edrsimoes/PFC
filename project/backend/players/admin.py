from django.contrib import admin

from .models import Player, PlayerAttributes


class PlayerAttributesInline(admin.StackedInline):
    model = PlayerAttributes
    can_delete = False


@admin.register(Player)
class PlayerAdmin(admin.ModelAdmin):
    list_display = ("nome", "usuario", "posicao", "overall", "clube_atual", "idade", "status")
    list_filter = ("posicao", "status", "perfil")
    search_fields = ("nome", "usuario__username")
    inlines = [PlayerAttributesInline]


@admin.register(PlayerAttributes)
class PlayerAttributesAdmin(admin.ModelAdmin):
    list_display = ("jogador",)
