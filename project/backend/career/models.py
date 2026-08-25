from django.db import models

from clubs.models import Club
from players.models import Player


class Season(models.Model):
    """Uma temporada da carreira de um jogador em um clube/competição principal."""

    jogador = models.ForeignKey(Player, on_delete=models.CASCADE, related_name="temporadas")
    ano = models.CharField(max_length=9, help_text="Ex: 2026/27")
    clube = models.ForeignKey(Club, on_delete=models.SET_NULL, null=True, related_name="temporadas")
    competicao_principal = models.CharField(max_length=120, default="Campeonato Nacional")

    jogos = models.PositiveSmallIntegerField(default=0)
    gols = models.PositiveSmallIntegerField(default=0)
    assistencias = models.PositiveSmallIntegerField(default=0)
    cartoes_amarelos = models.PositiveSmallIntegerField(default=0)
    cartoes_vermelhos = models.PositiveSmallIntegerField(default=0)
    nota_media = models.DecimalField(max_digits=3, decimal_places=1, default=6.0)

    overall_inicio = models.PositiveSmallIntegerField(null=True, blank=True)
    overall_fim = models.PositiveSmallIntegerField(null=True, blank=True)

    encerrada = models.BooleanField(default=False)
    criada_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Temporada"
        verbose_name_plural = "Temporadas"
        ordering = ["-ano"]
        unique_together = ("jogador", "ano")

    def __str__(self):
        return f"{self.jogador.nome} - {self.ano}"


class Training(models.Model):
    """Registro de uma sessão de treinamento."""

    class Tipo(models.TextChoices):
        FINALIZACAO = "finalizacao", "Treino de Finalização"
        FISICO = "fisico", "Treino Físico"
        VELOCIDADE = "velocidade", "Treino de Velocidade"
        PASSE = "passe", "Treino de Passe"
        DRIBLE = "drible", "Treino de Drible"
        DEFENSIVO = "defensivo", "Treino Defensivo"

    jogador = models.ForeignKey(Player, on_delete=models.CASCADE, related_name="treinos")
    tipo = models.CharField(max_length=20, choices=Tipo.choices)
    energia_consumida = models.PositiveSmallIntegerField(default=15)
    ganhos = models.JSONField(default=dict, help_text="Ex: {'finalizacao': 2, 'velocidade': 1}")
    realizado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Treinamento"
        verbose_name_plural = "Treinamentos"
        ordering = ["-realizado_em"]

    def __str__(self):
        return f"{self.get_tipo_display()} - {self.jogador.nome}"


class Achievement(models.Model):
    """Definição de uma conquista disponível no jogo (catálogo fixo)."""

    codigo = models.SlugField(max_length=60, unique=True)
    titulo = models.CharField(max_length=120)
    descricao = models.CharField(max_length=255)
    icone = models.CharField(max_length=10, default="🏆")

    class Meta:
        verbose_name = "Conquista"
        verbose_name_plural = "Conquistas"

    def __str__(self):
        return f"{self.icone} {self.titulo}"


class PlayerAchievement(models.Model):
    """Conquista desbloqueada por um jogador específico."""

    jogador = models.ForeignKey(Player, on_delete=models.CASCADE, related_name="conquistas")
    achievement = models.ForeignKey(Achievement, on_delete=models.CASCADE, related_name="desbloqueios")
    desbloqueada_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Conquista do Jogador"
        verbose_name_plural = "Conquistas dos Jogadores"
        unique_together = ("jogador", "achievement")
        ordering = ["-desbloqueada_em"]

    def __str__(self):
        return f"{self.jogador.nome} - {self.achievement.titulo}"


class CareerHistory(models.Model):
    """Linha do tempo de marcos importantes da carreira."""

    jogador = models.ForeignKey(Player, on_delete=models.CASCADE, related_name="historico")
    ano = models.CharField(max_length=9)
    titulo = models.CharField(max_length=150)
    descricao = models.CharField(max_length=255, blank=True)
    clube = models.ForeignKey(Club, on_delete=models.SET_NULL, null=True, blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Histórico de Carreira"
        verbose_name_plural = "Históricos de Carreira"
        ordering = ["-criado_em"]

    def __str__(self):
        return f"{self.ano} - {self.titulo}"


class News(models.Model):
    """Notícia gerada dinamicamente a partir de acontecimentos da carreira."""

    jogador = models.ForeignKey(Player, on_delete=models.CASCADE, related_name="noticias")
    titulo = models.CharField(max_length=200)
    corpo = models.TextField(blank=True)
    categoria = models.CharField(
        max_length=30,
        choices=[
            ("partida", "Partida"), ("transferencia", "Transferência"),
            ("selecao", "Seleção"), ("lesao", "Lesão"), ("premio", "Prêmio"),
            ("contrato", "Contrato"), ("geral", "Geral"),
        ],
        default="geral",
    )
    publicada_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Notícia"
        verbose_name_plural = "Notícias"
        ordering = ["-publicada_em"]

    def __str__(self):
        return self.titulo


class DecisionEvent(models.Model):
    """Evento de decisão apresentado ao jogador durante a carreira."""

    codigo = models.SlugField(max_length=80, unique=True)
    titulo = models.CharField(max_length=150)
    descricao = models.TextField()
    contexto = models.CharField(
        max_length=30,
        choices=[
            ("treino", "Treino"), ("partida", "Partida"), ("clube", "Clube"),
            ("imprensa", "Imprensa"), ("transferencia", "Transferência"),
            ("pessoal", "Pessoal"),
        ],
        default="clube",
    )

    class Meta:
        verbose_name = "Evento de Decisão"
        verbose_name_plural = "Eventos de Decisão"

    def __str__(self):
        return self.titulo


class DecisionOption(models.Model):
    """Opção de escolha dentro de um DecisionEvent, com seus efeitos."""

    evento = models.ForeignKey(DecisionEvent, on_delete=models.CASCADE, related_name="opcoes")
    letra = models.CharField(max_length=2, help_text="Ex: A, B, C")
    texto = models.CharField(max_length=200)

    efeito_moral = models.SmallIntegerField(default=0)
    efeito_reputacao = models.SmallIntegerField(default=0)
    efeito_relacao_treinador = models.SmallIntegerField(default=0)
    efeito_relacao_torcida = models.SmallIntegerField(default=0)
    efeito_valor_mercado_percentual = models.SmallIntegerField(
        default=0, help_text="Variação percentual no valor de mercado, ex: 5 = +5%."
    )

    class Meta:
        verbose_name = "Opção de Decisão"
        verbose_name_plural = "Opções de Decisão"
        ordering = ["letra"]

    def __str__(self):
        return f"{self.letra}) {self.texto}"


class DecisionLog(models.Model):
    """Registro de qual opção o jogador escolheu em cada evento de decisão."""

    jogador = models.ForeignKey(Player, on_delete=models.CASCADE, related_name="decisoes_tomadas")
    evento = models.ForeignKey(DecisionEvent, on_delete=models.CASCADE)
    opcao_escolhida = models.ForeignKey(DecisionOption, on_delete=models.CASCADE)
    decidido_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Registro de Decisão"
        verbose_name_plural = "Registros de Decisão"
        ordering = ["-decidido_em"]

    def __str__(self):
        return f"{self.jogador.nome} - {self.evento.titulo}"
