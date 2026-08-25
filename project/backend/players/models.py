from django.conf import settings
from django.db import models

from clubs.models import Club

# Pesos de cada atributo por posição, usados para calcular o overall.
# A soma dos pesos de cada posição é 1.0.
PESOS_OVERALL_POR_POSICAO = {
    "goleiro": {
        "defesa": 0.35, "posicionamento": 0.25, "fisico": 0.15,
        "inteligencia": 0.15, "forca": 0.10,
    },
    "zagueiro": {
        "defesa": 0.35, "forca": 0.20, "posicionamento": 0.20,
        "fisico": 0.15, "passe": 0.10,
    },
    "lateral_esquerdo": {
        "velocidade": 0.20, "defesa": 0.20, "passe": 0.15,
        "fisico": 0.15, "drible": 0.15, "aceleracao": 0.15,
    },
    "lateral_direito": {
        "velocidade": 0.20, "defesa": 0.20, "passe": 0.15,
        "fisico": 0.15, "drible": 0.15, "aceleracao": 0.15,
    },
    "volante": {
        "passe": 0.25, "defesa": 0.25, "inteligencia": 0.20,
        "fisico": 0.15, "posicionamento": 0.15,
    },
    "meia": {
        "passe": 0.30, "inteligencia": 0.20, "drible": 0.20,
        "velocidade": 0.15, "finalizacao": 0.15,
    },
    "meia_atacante": {
        "finalizacao": 0.20, "passe": 0.25, "drible": 0.25,
        "inteligencia": 0.15, "velocidade": 0.15,
    },
    "ponta_esquerda": {
        "velocidade": 0.25, "drible": 0.25, "finalizacao": 0.20,
        "aceleracao": 0.15, "passe": 0.15,
    },
    "ponta_direita": {
        "velocidade": 0.25, "drible": 0.25, "finalizacao": 0.20,
        "aceleracao": 0.15, "passe": 0.15,
    },
    "segundo_atacante": {
        "finalizacao": 0.30, "drible": 0.20, "velocidade": 0.20,
        "passe": 0.15, "inteligencia": 0.15,
    },
    "atacante": {
        "finalizacao": 0.35, "velocidade": 0.20, "drible": 0.20,
        "forca": 0.10, "passe": 0.15,
    },
}

PERFIS_INICIAIS = {
    # Cada perfil dá um "empurrão" inicial em alguns atributos na criação.
    "finalizador": {"finalizacao": 15, "posicionamento": 10},
    "velocista": {"velocidade": 15, "aceleracao": 15},
    "criador": {"passe": 15, "inteligencia": 10},
    "driblador": {"drible": 15, "aceleracao": 10},
    "defensor": {"defesa": 15, "forca": 10},
    "completo": {
        "velocidade": 4, "aceleracao": 4, "finalizacao": 4, "passe": 4,
        "drible": 4, "forca": 4, "defesa": 4, "fisico": 4, "inteligencia": 4,
        "posicionamento": 4,
    },
}


class Player(models.Model):
    class Posicao(models.TextChoices):
        GOLEIRO = "goleiro", "Goleiro"
        ZAGUEIRO = "zagueiro", "Zagueiro"
        LATERAL_ESQUERDO = "lateral_esquerdo", "Lateral Esquerdo"
        LATERAL_DIREITO = "lateral_direito", "Lateral Direito"
        VOLANTE = "volante", "Volante"
        MEIA = "meia", "Meia"
        MEIA_ATACANTE = "meia_atacante", "Meia Atacante"
        PONTA_ESQUERDA = "ponta_esquerda", "Ponta Esquerda"
        PONTA_DIREITA = "ponta_direita", "Ponta Direita"
        SEGUNDO_ATACANTE = "segundo_atacante", "Segundo Atacante"
        ATACANTE = "atacante", "Atacante"

    class Perfil(models.TextChoices):
        FINALIZADOR = "finalizador", "Finalizador"
        VELOCISTA = "velocista", "Velocista"
        CRIADOR = "criador", "Criador"
        DRIBLADOR = "driblador", "Driblador"
        DEFENSOR = "defensor", "Defensor"
        COMPLETO = "completo", "Completo"

    class PeDominante(models.TextChoices):
        DIREITO = "direito", "Direito"
        ESQUERDO = "esquerdo", "Esquerdo"
        AMBIDESTRO = "ambidestro", "Ambidestro"

    class Status(models.TextChoices):
        ATIVO = "ativo", "Ativo"
        LESIONADO = "lesionado", "Lesionado"
        APOSENTADO = "aposentado", "Aposentado"

    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="jogador"
    )
    nome = models.CharField(max_length=120)
    apelido = models.CharField(max_length=60, blank=True)
    idade = models.PositiveSmallIntegerField(default=17)
    nacionalidade = models.CharField(max_length=80)
    altura = models.PositiveSmallIntegerField(help_text="Altura em centímetros.", default=178)
    pe_dominante = models.CharField(max_length=12, choices=PeDominante.choices, default=PeDominante.DIREITO)
    posicao = models.CharField(max_length=20, choices=Posicao.choices)
    perfil = models.CharField(max_length=20, choices=Perfil.choices, default=Perfil.COMPLETO)

    clube_atual = models.ForeignKey(
        Club, on_delete=models.SET_NULL, null=True, blank=True, related_name="elenco"
    )
    status = models.CharField(max_length=15, choices=Status.choices, default=Status.ATIVO)

    overall = models.PositiveSmallIntegerField(default=50)
    forma_atual = models.SmallIntegerField(
        default=0, help_text="-10 a +10, afeta desempenho nas partidas."
    )
    condicao_fisica = models.PositiveSmallIntegerField(
        default=100, help_text="0-100, energia disponível para jogar/treinar."
    )
    moral = models.PositiveSmallIntegerField(default=70, help_text="0-100.")
    reputacao = models.PositiveSmallIntegerField(default=10, help_text="0-100.")

    valor_mercado = models.BigIntegerField(default=100_000)
    salario_semanal = models.BigIntegerField(default=1_000)
    saldo = models.BigIntegerField(default=0, help_text="Saldo acumulado do jogador (prêmios, salários recebidos).")

    convocado_selecao = models.BooleanField(default=False)
    temporada_atual = models.CharField(max_length=9, default="2026/27")

    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Jogador"
        verbose_name_plural = "Jogadores"
        ordering = ["-overall"]

    def __str__(self):
        return f"{self.nome} ({self.get_posicao_display()}) - OVR {self.overall}"

    @property
    def nome_exibicao(self):
        return self.apelido or self.nome

    def calcular_overall(self, salvar=True):
        """
        Calcula o overall com base nos atributos e nos pesos da posição.
        Regra de negócio central do jogo - deve rodar SEMPRE no backend.
        """
        try:
            atributos = self.atributos
        except PlayerAttributes.DoesNotExist:
            return self.overall

        pesos = PESOS_OVERALL_POR_POSICAO.get(self.posicao, {})
        if not pesos:
            return self.overall

        total = 0.0
        for atributo, peso in pesos.items():
            total += getattr(atributos, atributo, 0) * peso

        novo_overall = round(total)
        novo_overall = max(1, min(99, novo_overall))

        if salvar and novo_overall != self.overall:
            self.overall = novo_overall
            self.save(update_fields=["overall"])

        return novo_overall


class PlayerAttributes(models.Model):
    """Atributos de 0 a 100 do jogador."""

    jogador = models.OneToOneField(Player, on_delete=models.CASCADE, related_name="atributos")

    velocidade = models.PositiveSmallIntegerField(default=50)
    aceleracao = models.PositiveSmallIntegerField(default=50)
    finalizacao = models.PositiveSmallIntegerField(default=50)
    passe = models.PositiveSmallIntegerField(default=50)
    drible = models.PositiveSmallIntegerField(default=50)
    forca = models.PositiveSmallIntegerField(default=50)
    defesa = models.PositiveSmallIntegerField(default=50)
    fisico = models.PositiveSmallIntegerField(default=50)
    inteligencia = models.PositiveSmallIntegerField(default=50)
    posicionamento = models.PositiveSmallIntegerField(default=50)

    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Atributos do Jogador"
        verbose_name_plural = "Atributos dos Jogadores"

    def __str__(self):
        return f"Atributos de {self.jogador.nome}"

    ATRIBUTOS_NOMES = [
        "velocidade", "aceleracao", "finalizacao", "passe", "drible",
        "forca", "defesa", "fisico", "inteligencia", "posicionamento",
    ]

    def aplicar_perfil_inicial(self, perfil, salvar=True):
        """Aplica o bônus de atributos do perfil escolhido na criação do jogador."""
        bonus = PERFIS_INICIAIS.get(perfil, {})
        for atributo, valor in bonus.items():
            atual = getattr(self, atributo, 0)
            setattr(self, atributo, min(99, atual + valor))
        if salvar:
            self.save()

    def evoluir(self, ganhos: dict, salvar=True):
        """
        Aplica pontos de evolução limitando cada atributo a 99 e evitando
        evolução exagerada (o chamador é responsável por definir ganhos
        razoáveis - ver players/evolution.py).
        """
        for atributo, pontos in ganhos.items():
            if atributo not in self.ATRIBUTOS_NOMES:
                continue
            atual = getattr(self, atributo)
            setattr(self, atributo, max(0, min(99, atual + pontos)))
        if salvar:
            self.save()
