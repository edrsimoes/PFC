import random

from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView

from career.models import (
    Achievement, CareerHistory, DecisionEvent, News, PlayerAchievement,
    Season, Training,
)
from clubs.models import Club, Competition, League
from matches.engine import simulate_match
from matches.models import Match, MatchEvent
from players.evolution import calcular_ganhos_treino, custo_energia
from players.models import Player
from transfers.models import Contract, Injury, Transfer

from .serializers import (
    AchievementSerializer, CareerHistorySerializer, ClubSerializer,
    CompetitionSerializer, ContractSerializer, DecisionEventSerializer,
    DecisionSubmitSerializer, InjurySerializer, LeagueSerializer,
    MatchSerializer, NewsSerializer, PlayerAchievementSerializer,
    PlayerCreateSerializer, PlayerSerializer, RegisterSerializer,
    SeasonSerializer, SimulateMatchSerializer, TrainingSerializer,
    TrainSerializer, TransferNegotiateSerializer, TransferSerializer,
)


# --------------------------------------------------------------------------
# Autenticação
# --------------------------------------------------------------------------

class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]


class CustomTokenObtainPairView(TokenObtainPairView):
    permission_classes = [permissions.AllowAny]


# --------------------------------------------------------------------------
# Utilitário: sempre buscar o jogador do usuário autenticado
# --------------------------------------------------------------------------

def _get_jogador_do_usuario(request):
    return get_object_or_404(Player, usuario=request.user)


# --------------------------------------------------------------------------
# Clubes / Ligas / Competições (dados de referência, somente leitura)
# --------------------------------------------------------------------------

class ClubListView(generics.ListAPIView):
    queryset = Club.objects.select_related("liga").all()
    serializer_class = ClubSerializer
    permission_classes = [permissions.IsAuthenticated]


class LeagueListView(generics.ListAPIView):
    queryset = League.objects.all()
    serializer_class = LeagueSerializer
    permission_classes = [permissions.IsAuthenticated]


class CompetitionListView(generics.ListAPIView):
    queryset = Competition.objects.all()
    serializer_class = CompetitionSerializer
    permission_classes = [permissions.IsAuthenticated]


# --------------------------------------------------------------------------
# Jogador
# --------------------------------------------------------------------------

class PlayerView(APIView):
    """
    GET  /api/player/  -> retorna o jogador do usuário autenticado (404 se não existe)
    POST /api/player/  -> cria o jogador (uma vez por usuário)
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        player = get_object_or_404(Player, usuario=request.user)
        return Response(PlayerSerializer(player).data)

    def post(self, request):
        if Player.objects.filter(usuario=request.user).exists():
            return Response(
                {"detail": "Você já possui uma carreira em andamento."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        serializer = PlayerCreateSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        player = serializer.save()
        return Response(PlayerSerializer(player).data, status=status.HTTP_201_CREATED)


class PlayerStatsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        player = _get_jogador_do_usuario(request)
        temporadas = Season.objects.filter(jogador=player).order_by("ano")
        historico_overall = [
            {"ano": t.ano, "overall": t.overall_fim or player.overall}
            for t in temporadas
        ]
        totais = {
            "jogos": sum(t.jogos for t in temporadas),
            "gols": sum(t.gols for t in temporadas),
            "assistencias": sum(t.assistencias for t in temporadas),
        }
        return Response({
            "jogador": PlayerSerializer(player).data,
            "temporadas": SeasonSerializer(temporadas, many=True).data,
            "historico_overall": historico_overall,
            "totais_carreira": totais,
        })


class PlayerTrainView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        player = _get_jogador_do_usuario(request)

        if player.status == Player.Status.LESIONADO:
            return Response(
                {"detail": "Jogador lesionado não pode treinar."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = TrainSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        tipo = serializer.validated_data["tipo"]

        energia_necessaria = custo_energia(tipo)
        if player.condicao_fisica < energia_necessaria:
            return Response(
                {"detail": "Condição física insuficiente para esse treino. Descanse antes."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        ganhos = calcular_ganhos_treino(tipo, player.idade)
        atributos = player.atributos
        atributos.evoluir(ganhos)

        player.condicao_fisica = max(0, player.condicao_fisica - energia_necessaria)
        player.save(update_fields=["condicao_fisica"])
        player.calcular_overall()

        treino = Training.objects.create(
            jogador=player, tipo=tipo, energia_consumida=energia_necessaria, ganhos=ganhos,
        )

        return Response({
            "treino": TrainingSerializer(treino).data,
            "jogador": PlayerSerializer(player).data,
        })


# --------------------------------------------------------------------------
# Carreira (histórico, achievements, notícias)
# --------------------------------------------------------------------------

class CareerView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        player = _get_jogador_do_usuario(request)
        historico = CareerHistory.objects.filter(jogador=player)
        conquistas = PlayerAchievement.objects.filter(jogador=player).select_related("achievement")
        noticias = News.objects.filter(jogador=player)[:20]
        return Response({
            "historico": CareerHistorySerializer(historico, many=True).data,
            "conquistas": PlayerAchievementSerializer(conquistas, many=True).data,
            "noticias": NewsSerializer(noticias, many=True).data,
        })


class AchievementListView(generics.ListAPIView):
    queryset = Achievement.objects.all()
    serializer_class = AchievementSerializer
    permission_classes = [permissions.IsAuthenticated]


# --------------------------------------------------------------------------
# Partidas
# --------------------------------------------------------------------------

class MatchListView(generics.ListAPIView):
    serializer_class = MatchSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        player = _get_jogador_do_usuario(self.request)
        return Match.objects.filter(jogador=player).prefetch_related("eventos")


def _desbloquear_conquista(player, codigo):
    try:
        achievement = Achievement.objects.get(codigo=codigo)
    except Achievement.DoesNotExist:
        return
    PlayerAchievement.objects.get_or_create(jogador=player, achievement=achievement)


class SimulateMatchView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        player = _get_jogador_do_usuario(request)

        if player.status == Player.Status.LESIONADO:
            return Response(
                {"detail": "Jogador lesionado não pode jogar."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = SimulateMatchSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        dados = serializer.validated_data

        temporada, _ = Season.objects.get_or_create(
            jogador=player, ano=player.temporada_atual,
            defaults={"clube": player.clube_atual},
        )

        resultado = simulate_match(
            player=player,
            forca_adversario=dados["forca_adversario"],
            importancia=dados["importancia"],
            mandante=dados["mandante"],
        )

        match = Match.objects.create(
            jogador=player, temporada=temporada, adversario=dados["adversario"],
            competicao=dados.get("competicao"), importancia=dados["importancia"],
            forca_adversario=dados["forca_adversario"], mandante=dados["mandante"],
            gols_time=resultado.gols_time, gols_adversario=resultado.gols_adversario,
            gols_jogador=resultado.gols_jogador,
            assistencias_jogador=resultado.assistencias_jogador,
            nota_jogador=resultado.nota_jogador, titular=resultado.titular,
            minutos_jogados=resultado.minutos_jogados,
        )
        for evento in resultado.eventos:
            MatchEvent.objects.create(partida=match, **evento)

        # Atualiza estatísticas da temporada.
        temporada.jogos += 1
        temporada.gols += resultado.gols_jogador
        temporada.assistencias += resultado.assistencias_jogador
        if temporada.overall_inicio is None:
            temporada.overall_inicio = player.overall
        temporada.overall_fim = player.overall
        # Média móvel simples de nota.
        total_jogos = temporada.jogos
        temporada.nota_media = (
            (temporada.nota_media * (total_jogos - 1)) + resultado.nota_jogador
        ) / total_jogos
        temporada.save()

        # Atualiza forma e condição física do jogador.
        if resultado.gols_jogador or resultado.assistencias_jogador:
            player.forma_atual = min(10, player.forma_atual + 2)
            player.moral = min(100, player.moral + 3)
        elif resultado.nota_jogador < 5.5:
            player.forma_atual = max(-10, player.forma_atual - 1)
        player.condicao_fisica = max(10, player.condicao_fisica - random.randint(15, 30))

        # Lesão.
        if resultado.lesionou:
            semanas = Injury.DURACAO_SEMANAS.get(resultado.gravidade_lesao, 2)
            Injury.objects.create(
                jogador=player, gravidade=resultado.gravidade_lesao,
                descricao="Lesão sofrida durante partida.",
                semanas_totais=semanas, semanas_restantes=semanas,
            )
            player.status = Player.Status.LESIONADO
            News.objects.create(
                jogador=player, categoria="lesao",
                titulo=f"{player.nome_exibicao} sofre lesão e desfalca o time",
                corpo=f"O jogador sofreu uma lesão do tipo '{resultado.gravidade_lesao}' durante a partida contra {dados['adversario']}.",
            )

        player.save()
        player.calcular_overall()

        # Notícia de destaque.
        if resultado.gols_jogador >= 2:
            News.objects.create(
                jogador=player, categoria="partida",
                titulo=f"{player.nome_exibicao} marca {resultado.gols_jogador} gols e brilha em campo",
                corpo=f"Atuação de gala contra {dados['adversario']}: {resultado.gols_jogador} gols e {resultado.assistencias_jogador} assistências.",
            )

        # Conquistas simples.
        if Match.objects.filter(jogador=player, gols_jogador__gte=1).count() == 1 and resultado.gols_jogador >= 1:
            _desbloquear_conquista(player, "primeiro-gol")
        if temporada.gols >= 10:
            _desbloquear_conquista(player, "dez-gols-temporada")

        return Response({
            "partida": MatchSerializer(match).data,
            "jogador": PlayerSerializer(player).data,
            "temporada": SeasonSerializer(temporada).data,
        }, status=status.HTTP_201_CREATED)


# --------------------------------------------------------------------------
# Transferências
# --------------------------------------------------------------------------

class TransferListView(generics.ListAPIView):
    serializer_class = TransferSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        player = _get_jogador_do_usuario(self.request)
        return Transfer.objects.filter(jogador=player).select_related("clube_destino")


def _gerar_valor_proposta(player, clube):
    base = player.valor_mercado
    variacao = random.uniform(0.85, 1.25)
    valor = int(base * variacao * (clube.prestigio / 60))
    salario = int(player.salario_semanal * random.uniform(1.1, 1.8))
    return max(50_000, valor), max(1_000, salario)


class TransferGenerateView(APIView):
    """Gera novas propostas de transferência com base no perfil do jogador."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        player = _get_jogador_do_usuario(request)

        candidatos = Club.objects.filter(
            overall_minimo__lte=player.overall + 5
        ).exclude(id=player.clube_atual_id if player.clube_atual_id else 0)

        interessados = [c for c in candidatos if c.overall_minimo <= player.overall + 8]
        random.shuffle(interessados)
        escolhidos = interessados[:random.randint(1, 3)]

        propostas = []
        for clube in escolhidos:
            valor, salario = _gerar_valor_proposta(player, clube)
            proposta = Transfer.objects.create(
                jogador=player, clube_origem=player.clube_atual, clube_destino=clube,
                valor=valor, salario_semanal_oferecido=salario,
                duracao_anos=random.choice([2, 3, 4]),
            )
            propostas.append(proposta)
            News.objects.create(
                jogador=player, categoria="transferencia",
                titulo=f"{clube.nome} demonstra interesse em {player.nome_exibicao}",
                corpo=f"Uma proposta de €{valor:,} foi enviada ao estafe do jogador.".replace(",", "."),
            )

        return Response(TransferSerializer(propostas, many=True).data, status=status.HTTP_201_CREATED)


class TransferAcceptView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        player = _get_jogador_do_usuario(request)
        proposta = get_object_or_404(Transfer, pk=pk, jogador=player)

        if proposta.status != Transfer.Status.PENDENTE and proposta.status != Transfer.Status.NEGOCIANDO:
            return Response({"detail": "Essa proposta não está mais disponível."}, status=400)

        Contract.objects.filter(jogador=player, ativo=True).update(ativo=False)
        Contract.objects.create(
            jogador=player, clube=proposta.clube_destino,
            salario_semanal=proposta.salario_semanal_oferecido,
            duracao_anos=proposta.duracao_anos,
            ano_inicio=int(player.temporada_atual[:4]),
            ano_fim=int(player.temporada_atual[:4]) + proposta.duracao_anos,
        )

        clube_antigo = player.clube_atual
        player.clube_atual = proposta.clube_destino
        player.salario_semanal = proposta.salario_semanal_oferecido
        player.valor_mercado = max(player.valor_mercado, proposta.valor)
        player.save()

        proposta.status = Transfer.Status.ACEITA
        proposta.respondida_em = timezone.now()
        proposta.save()

        CareerHistory.objects.create(
            jogador=player, ano=player.temporada_atual, titulo="Transferência",
            descricao=f"{player.nome_exibicao} deixa o {clube_antigo.nome if clube_antigo else '—'} e assina com o {proposta.clube_destino.nome}.",
            clube=proposta.clube_destino,
        )
        News.objects.create(
            jogador=player, categoria="transferencia",
            titulo=f"Fechado! {player.nome_exibicao} é o novo reforço do {proposta.clube_destino.nome}",
            corpo=f"Transferência confirmada por €{proposta.valor:,}".replace(",", "."),
        )
        if proposta.valor >= 20_000_000:
            _desbloquear_conquista(player, "transferencia-milionaria")

        return Response({
            "proposta": TransferSerializer(proposta).data,
            "jogador": PlayerSerializer(player).data,
        })


class TransferRejectView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        player = _get_jogador_do_usuario(request)
        proposta = get_object_or_404(Transfer, pk=pk, jogador=player)
        proposta.status = Transfer.Status.RECUSADA
        proposta.save()
        return Response(TransferSerializer(proposta).data)


class TransferNegotiateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        player = _get_jogador_do_usuario(request)
        proposta = get_object_or_404(Transfer, pk=pk, jogador=player)

        if proposta.rodadas_negociacao >= 3:
            return Response({"detail": "O clube não fará mais concessões."}, status=400)

        serializer = TransferNegotiateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        aceita_negociar = random.random() < 0.6
        if aceita_negociar:
            proposta.valor = int(proposta.valor * random.uniform(1.03, 1.12))
            proposta.salario_semanal_oferecido = int(
                proposta.salario_semanal_oferecido * random.uniform(1.03, 1.10)
            )
            proposta.status = Transfer.Status.NEGOCIANDO
        proposta.rodadas_negociacao += 1
        proposta.save()

        return Response({
            "aceitou_negociar": aceita_negociar,
            "proposta": TransferSerializer(proposta).data,
        })


# --------------------------------------------------------------------------
# Contratos e Lesões
# --------------------------------------------------------------------------

class ContractListView(generics.ListAPIView):
    serializer_class = ContractSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        player = _get_jogador_do_usuario(self.request)
        return Contract.objects.filter(jogador=player).select_related("clube")


class InjuryListView(generics.ListAPIView):
    serializer_class = InjurySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        player = _get_jogador_do_usuario(self.request)
        return Injury.objects.filter(jogador=player)


# --------------------------------------------------------------------------
# Decisões
# --------------------------------------------------------------------------

class DecisionEventListView(generics.ListAPIView):
    queryset = DecisionEvent.objects.prefetch_related("opcoes").all()
    serializer_class = DecisionEventSerializer
    permission_classes = [permissions.IsAuthenticated]


class DecisionSubmitView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        player = _get_jogador_do_usuario(request)
        serializer = DecisionSubmitSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        opcao = serializer.validated_data["opcao_id"]
        evento = serializer.validated_data["evento_id"]

        player.moral = max(0, min(100, player.moral + opcao.efeito_moral))
        player.reputacao = max(0, min(100, player.reputacao + opcao.efeito_reputacao))
        if opcao.efeito_valor_mercado_percentual:
            player.valor_mercado = max(
                10_000,
                int(player.valor_mercado * (1 + opcao.efeito_valor_mercado_percentual / 100)),
            )
        player.save()

        from career.models import DecisionLog
        DecisionLog.objects.create(jogador=player, evento=evento, opcao_escolhida=opcao)

        return Response({
            "jogador": PlayerSerializer(player).data,
            "opcao_escolhida": opcao.texto,
        })
