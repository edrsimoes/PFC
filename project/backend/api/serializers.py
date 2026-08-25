from django.contrib.auth import get_user_model
from rest_framework import serializers

from career.models import (
    Achievement, CareerHistory, DecisionEvent, DecisionOption, News,
    PlayerAchievement, Season, Training,
)
from clubs.models import Club, Competition, League
from matches.models import Match, MatchEvent
from players.models import Player, PlayerAttributes
from transfers.models import Contract, Injury, Transfer

User = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=6)

    class Meta:
        model = User
        fields = ["id", "username", "email", "password"]

    def create(self, validated_data):
        return User.objects.create_user(
            username=validated_data["username"],
            email=validated_data.get("email", ""),
            password=validated_data["password"],
        )


class ClubSerializer(serializers.ModelSerializer):
    class Meta:
        model = Club
        fields = [
            "id", "nome", "pais", "liga", "overall_minimo", "orcamento",
            "prestigio", "escudo_cor_primaria", "escudo_cor_secundaria",
        ]


class LeagueSerializer(serializers.ModelSerializer):
    class Meta:
        model = League
        fields = ["id", "nome", "pais", "nivel", "prestigio"]


class CompetitionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Competition
        fields = ["id", "nome", "tipo", "continente", "prestigio"]


class PlayerAttributesSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlayerAttributes
        fields = [
            "velocidade", "aceleracao", "finalizacao", "passe", "drible",
            "forca", "defesa", "fisico", "inteligencia", "posicionamento",
        ]


class PlayerSerializer(serializers.ModelSerializer):
    atributos = PlayerAttributesSerializer(read_only=True)
    clube_atual_nome = serializers.CharField(source="clube_atual.nome", read_only=True, default=None)
    nome_exibicao = serializers.CharField(read_only=True)

    class Meta:
        model = Player
        fields = [
            "id", "nome", "apelido", "nome_exibicao", "idade", "nacionalidade",
            "altura", "pe_dominante", "posicao", "perfil", "clube_atual",
            "clube_atual_nome", "status", "overall", "forma_atual",
            "condicao_fisica", "moral", "reputacao", "valor_mercado",
            "salario_semanal", "saldo", "convocado_selecao",
            "temporada_atual", "atributos", "criado_em",
        ]
        read_only_fields = [
            "overall", "forma_atual", "reputacao", "valor_mercado", "saldo",
            "convocado_selecao", "status",
        ]


class PlayerCreateSerializer(serializers.Serializer):
    """
    Serializer dedicado à criação do jogador: recebe os dados básicos +
    perfil inicial + clube inicial, e monta Player e PlayerAttributes de
    forma consistente (todo o cálculo acontece no backend).
    """

    nome = serializers.CharField(max_length=120)
    apelido = serializers.CharField(max_length=60, required=False, allow_blank=True)
    idade = serializers.IntegerField(min_value=16, max_value=21, default=17)
    nacionalidade = serializers.CharField(max_length=80)
    altura = serializers.IntegerField(min_value=150, max_value=210, default=178)
    pe_dominante = serializers.ChoiceField(choices=Player.PeDominante.choices)
    posicao = serializers.ChoiceField(choices=Player.Posicao.choices)
    perfil = serializers.ChoiceField(choices=Player.Perfil.choices)
    clube_inicial_id = serializers.PrimaryKeyRelatedField(
        source="clube_inicial", queryset=Club.objects.all()
    )

    def create(self, validated_data):
        usuario = self.context["request"].user
        clube = validated_data.pop("clube_inicial")
        perfil = validated_data["perfil"]

        player = Player.objects.create(
            usuario=usuario,
            clube_atual=clube,
            valor_mercado=150_000,
            salario_semanal=2_000,
            **validated_data,
        )
        atributos = PlayerAttributes.objects.create(jogador=player)
        atributos.aplicar_perfil_inicial(perfil)
        player.calcular_overall()

        Season.objects.get_or_create(
            jogador=player, ano=player.temporada_atual,
            defaults={"clube": clube},
        )
        CareerHistory.objects.create(
            jogador=player, ano=player.temporada_atual, titulo="Início da carreira",
            descricao=f"{player.nome_exibicao} assina seu primeiro contrato profissional com o {clube.nome}.",
            clube=clube,
        )
        return player


class SeasonSerializer(serializers.ModelSerializer):
    clube_nome = serializers.CharField(source="clube.nome", read_only=True, default=None)

    class Meta:
        model = Season
        fields = [
            "id", "ano", "clube", "clube_nome", "competicao_principal",
            "jogos", "gols", "assistencias", "cartoes_amarelos",
            "cartoes_vermelhos", "nota_media", "overall_inicio",
            "overall_fim", "encerrada",
        ]


class TrainingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Training
        fields = ["id", "tipo", "energia_consumida", "ganhos", "realizado_em"]


class TrainSerializer(serializers.Serializer):
    tipo = serializers.ChoiceField(choices=Training.Tipo.choices)


class AchievementSerializer(serializers.ModelSerializer):
    class Meta:
        model = Achievement
        fields = ["id", "codigo", "titulo", "descricao", "icone"]


class PlayerAchievementSerializer(serializers.ModelSerializer):
    achievement = AchievementSerializer(read_only=True)

    class Meta:
        model = PlayerAchievement
        fields = ["id", "achievement", "desbloqueada_em"]


class CareerHistorySerializer(serializers.ModelSerializer):
    clube_nome = serializers.CharField(source="clube.nome", read_only=True, default=None)

    class Meta:
        model = CareerHistory
        fields = ["id", "ano", "titulo", "descricao", "clube", "clube_nome", "criado_em"]


class NewsSerializer(serializers.ModelSerializer):
    class Meta:
        model = News
        fields = ["id", "titulo", "corpo", "categoria", "publicada_em"]


class DecisionOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = DecisionOption
        fields = ["id", "letra", "texto"]


class DecisionEventSerializer(serializers.ModelSerializer):
    opcoes = DecisionOptionSerializer(many=True, read_only=True)

    class Meta:
        model = DecisionEvent
        fields = ["id", "codigo", "titulo", "descricao", "contexto", "opcoes"]


class DecisionSubmitSerializer(serializers.Serializer):
    evento_id = serializers.PrimaryKeyRelatedField(queryset=DecisionEvent.objects.all())
    opcao_id = serializers.PrimaryKeyRelatedField(queryset=DecisionOption.objects.all())

    def validate(self, attrs):
        if attrs["opcao_id"].evento_id != attrs["evento_id"].id:
            raise serializers.ValidationError("A opção escolhida não pertence a esse evento.")
        return attrs


class MatchEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = MatchEvent
        fields = ["id", "minuto", "tipo", "descricao", "escolha_disponivel", "escolha_feita"]


class MatchSerializer(serializers.ModelSerializer):
    eventos = MatchEventSerializer(many=True, read_only=True)

    class Meta:
        model = Match
        fields = [
            "id", "temporada", "adversario", "competicao", "importancia",
            "forca_adversario", "mandante", "gols_time", "gols_adversario",
            "gols_jogador", "assistencias_jogador", "nota_jogador",
            "titular", "minutos_jogados", "resultado", "eventos", "simulada_em",
        ]


class SimulateMatchSerializer(serializers.Serializer):
    adversario = serializers.CharField(max_length=120)
    forca_adversario = serializers.IntegerField(min_value=30, max_value=99)
    importancia = serializers.ChoiceField(choices=Match.Importancia.choices, default=Match.Importancia.NORMAL)
    mandante = serializers.BooleanField(default=True)
    competicao_id = serializers.PrimaryKeyRelatedField(
        source="competicao", queryset=Competition.objects.all(), required=False, allow_null=True
    )


class ContractSerializer(serializers.ModelSerializer):
    clube_nome = serializers.CharField(source="clube.nome", read_only=True)

    class Meta:
        model = Contract
        fields = [
            "id", "clube", "clube_nome", "salario_semanal", "duracao_anos",
            "ano_inicio", "ano_fim", "clausula_rescisoria", "ativo",
        ]


class InjurySerializer(serializers.ModelSerializer):
    class Meta:
        model = Injury
        fields = [
            "id", "gravidade", "descricao", "semanas_totais",
            "semanas_restantes", "penalidade_fisico_temporaria",
            "ocorrida_em", "recuperada",
        ]


class TransferSerializer(serializers.ModelSerializer):
    clube_destino_nome = serializers.CharField(source="clube_destino.nome", read_only=True)

    class Meta:
        model = Transfer
        fields = [
            "id", "clube_destino", "clube_destino_nome", "valor",
            "salario_semanal_oferecido", "duracao_anos", "status",
            "rodadas_negociacao", "criada_em", "respondida_em",
        ]
        read_only_fields = ["status", "rodadas_negociacao", "respondida_em"]


class TransferNegotiateSerializer(serializers.Serializer):
    valor_desejado = serializers.IntegerField(min_value=0, required=False)
    salario_desejado = serializers.IntegerField(min_value=0, required=False)
