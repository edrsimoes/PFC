from django.db import models

from career.models import Season
from clubs.models import Competition
from players.models import Player


class Match(models.Model):
    """Uma partida simulada da carreira do jogador."""

    class Importancia(models.TextChoices):
        NORMAL = "normal", "Normal"
        DECISIVA = "decisiva", "Decisiva"
        FINAL = "final", "Final"
        CLASSICO = "classico", "Clássico"

    jogador = models.ForeignKey(Player, on_delete=models.CASCADE, related_name="partidas")
    temporada = models.ForeignKey(Season, on_delete=models.CASCADE, related_name="partidas")
    adversario = models.CharField(max_length=120)
    competicao = models.ForeignKey(Competition, on_delete=models.SET_NULL, null=True, blank=True)
    importancia = models.CharField(max_length=10, choices=Importancia.choices, default=Importancia.NORMAL)

    forca_adversario = models.PositiveSmallIntegerField(default=60)
    mandante = models.BooleanField(default=True)

    gols_time = models.PositiveSmallIntegerField(default=0)
    gols_adversario = models.PositiveSmallIntegerField(default=0)

    gols_jogador = models.PositiveSmallIntegerField(default=0)
    assistencias_jogador = models.PositiveSmallIntegerField(default=0)
    nota_jogador = models.DecimalField(max_digits=3, decimal_places=1, default=6.0)
    titular = models.BooleanField(default=True)
    minutos_jogados = models.PositiveSmallIntegerField(default=90)

    simulada_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Partida"
        verbose_name_plural = "Partidas"
        ordering = ["-simulada_em"]

    def __str__(self):
        return f"{self.jogador.nome} vs {self.adversario} ({self.gols_time}x{self.gols_adversario})"

    @property
    def resultado(self):
        if self.gols_time > self.gols_adversario:
            return "vitoria"
        if self.gols_time < self.gols_adversario:
            return "derrota"
        return "empate"


class MatchEvent(models.Model):
    """Evento pontual dentro de uma partida (usado para narrar a simulação)."""

    class Tipo(models.TextChoices):
        GOL = "gol", "Gol"
        ASSISTENCIA = "assistencia", "Assistência"
        CHANCE = "chance", "Chance de Gol"
        DECISAO = "decisao", "Decisão do Jogador"
        CARTAO = "cartao", "Cartão"
        LESAO = "lesao", "Lesão"
        SUBSTITUICAO = "substituicao", "Substituição"
        NARRACAO = "narracao", "Narração"

    partida = models.ForeignKey(Match, on_delete=models.CASCADE, related_name="eventos")
    minuto = models.PositiveSmallIntegerField()
    tipo = models.CharField(max_length=20, choices=Tipo.choices)
    descricao = models.CharField(max_length=255)
    escolha_disponivel = models.JSONField(
        null=True, blank=True,
        help_text="Lista de opções apresentadas ao jogador nesse minuto, se houver.",
    )
    escolha_feita = models.CharField(max_length=50, blank=True)

    class Meta:
        verbose_name = "Evento de Partida"
        verbose_name_plural = "Eventos de Partida"
        ordering = ["minuto"]

    def __str__(self):
        return f"{self.minuto}' - {self.descricao}"
