from django.db import models

from clubs.models import Club
from players.models import Player


class Contract(models.Model):
    """Contrato vigente (ou passado) de um jogador com um clube."""

    jogador = models.ForeignKey(Player, on_delete=models.CASCADE, related_name="contratos")
    clube = models.ForeignKey(Club, on_delete=models.CASCADE, related_name="contratos")
    salario_semanal = models.BigIntegerField()
    duracao_anos = models.PositiveSmallIntegerField()
    ano_inicio = models.PositiveSmallIntegerField()
    ano_fim = models.PositiveSmallIntegerField()
    clausula_rescisoria = models.BigIntegerField(null=True, blank=True)
    ativo = models.BooleanField(default=True)
    assinado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Contrato"
        verbose_name_plural = "Contratos"
        ordering = ["-assinado_em"]

    def __str__(self):
        return f"{self.jogador.nome} - {self.clube.nome} ({self.ano_inicio}-{self.ano_fim})"


class Transfer(models.Model):
    """Proposta/negociação de transferência recebida pelo jogador."""

    class Status(models.TextChoices):
        PENDENTE = "pendente", "Pendente"
        ACEITA = "aceita", "Aceita"
        RECUSADA = "recusada", "Recusada"
        NEGOCIANDO = "negociando", "Em Negociação"
        EXPIRADA = "expirada", "Expirada"

    jogador = models.ForeignKey(Player, on_delete=models.CASCADE, related_name="propostas")
    clube_origem = models.ForeignKey(
        Club, on_delete=models.SET_NULL, null=True, blank=True, related_name="propostas_enviadas"
    )
    clube_destino = models.ForeignKey(Club, on_delete=models.CASCADE, related_name="propostas_recebidas")

    valor = models.BigIntegerField()
    salario_semanal_oferecido = models.BigIntegerField()
    duracao_anos = models.PositiveSmallIntegerField()

    status = models.CharField(max_length=12, choices=Status.choices, default=Status.PENDENTE)
    rodadas_negociacao = models.PositiveSmallIntegerField(default=0)

    criada_em = models.DateTimeField(auto_now_add=True)
    respondida_em = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Transferência"
        verbose_name_plural = "Transferências"
        ordering = ["-criada_em"]

    def __str__(self):
        return f"{self.jogador.nome} -> {self.clube_destino.nome} ({self.get_status_display()})"


class Injury(models.Model):
    """Lesão sofrida pelo jogador."""

    class Gravidade(models.TextChoices):
        MUSCULAR = "muscular", "Lesão Muscular"
        ENTORSE = "entorse", "Entorse"
        GRAVE = "grave", "Lesão Grave"

    DURACAO_SEMANAS = {
        Gravidade.MUSCULAR: 2,
        Gravidade.ENTORSE: 4,
        Gravidade.GRAVE: 16,
    }

    jogador = models.ForeignKey(Player, on_delete=models.CASCADE, related_name="lesoes")
    gravidade = models.CharField(max_length=10, choices=Gravidade.choices)
    descricao = models.CharField(max_length=200, blank=True)
    semanas_totais = models.PositiveSmallIntegerField()
    semanas_restantes = models.PositiveSmallIntegerField()
    penalidade_fisico_temporaria = models.SmallIntegerField(
        default=5, help_text="Quanto o atributo físico cai temporariamente durante a lesão."
    )
    ocorrida_em = models.DateTimeField(auto_now_add=True)
    recuperada = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Lesão"
        verbose_name_plural = "Lesões"
        ordering = ["-ocorrida_em"]

    def __str__(self):
        return f"{self.jogador.nome} - {self.get_gravidade_display()}"

    def avancar_semana(self):
        """Avança uma semana de recuperação; retorna True se recuperou totalmente."""
        if self.semanas_restantes > 0:
            self.semanas_restantes -= 1
        if self.semanas_restantes <= 0:
            self.recuperada = True
        self.save()
        return self.recuperada
