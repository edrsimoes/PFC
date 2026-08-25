from django.contrib import admin

from .models import Contract, Injury, Transfer


@admin.register(Contract)
class ContractAdmin(admin.ModelAdmin):
    list_display = ("jogador", "clube", "salario_semanal", "ano_inicio", "ano_fim", "ativo")
    list_filter = ("ativo",)


@admin.register(Transfer)
class TransferAdmin(admin.ModelAdmin):
    list_display = ("jogador", "clube_destino", "valor", "status", "criada_em")
    list_filter = ("status",)


@admin.register(Injury)
class InjuryAdmin(admin.ModelAdmin):
    list_display = ("jogador", "gravidade", "semanas_restantes", "recuperada")
    list_filter = ("gravidade", "recuperada")
