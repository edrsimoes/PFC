from django.db import models


class League(models.Model):
    """Liga nacional (ex: Campeonato Brasileiro, Premier League)."""

    nome = models.CharField(max_length=120)
    pais = models.CharField(max_length=80)
    nivel = models.PositiveSmallIntegerField(
        default=1, help_text="1 = elite, 2 = segunda divisão, etc."
    )
    prestigio = models.PositiveSmallIntegerField(
        default=50, help_text="0-100, usado para calcular reputação e propostas."
    )

    class Meta:
        verbose_name = "Liga"
        verbose_name_plural = "Ligas"
        ordering = ["-prestigio", "nome"]

    def __str__(self):
        return f"{self.nome} ({self.pais})"


class Competition(models.Model):
    """Competições continentais/copas (Libertadores, Champions League, etc.)."""

    class Tipo(models.TextChoices):
        CONTINENTAL = "continental", "Continental"
        COPA_NACIONAL = "copa_nacional", "Copa Nacional"
        SELECAO = "selecao", "Seleção"

    nome = models.CharField(max_length=120)
    tipo = models.CharField(max_length=20, choices=Tipo.choices)
    continente = models.CharField(max_length=40, blank=True)
    prestigio = models.PositiveSmallIntegerField(default=50)

    class Meta:
        verbose_name = "Competição"
        verbose_name_plural = "Competições"
        ordering = ["-prestigio", "nome"]

    def __str__(self):
        return self.nome


class Club(models.Model):
    """Clube que o jogador pode representar."""

    nome = models.CharField(max_length=120)
    pais = models.CharField(max_length=80)
    liga = models.ForeignKey(
        League, on_delete=models.SET_NULL, null=True, blank=True, related_name="clubes"
    )
    overall_minimo = models.PositiveSmallIntegerField(
        default=55, help_text="Overall mínimo aproximado do elenco - usado para gerar propostas coerentes."
    )
    orcamento = models.BigIntegerField(default=10_000_000, help_text="Orçamento de mercado em euros.")
    prestigio = models.PositiveSmallIntegerField(default=50)
    escudo_cor_primaria = models.CharField(max_length=7, default="#1e293b")
    escudo_cor_secundaria = models.CharField(max_length=7, default="#f8fafc")
    competicoes = models.ManyToManyField(Competition, blank=True, related_name="clubes")

    class Meta:
        verbose_name = "Clube"
        verbose_name_plural = "Clubes"
        ordering = ["-prestigio", "nome"]

    def __str__(self):
        return f"{self.nome} ({self.pais})"
