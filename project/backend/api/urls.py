from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from . import views

urlpatterns = [
    # Autenticação
    path("auth/register/", views.RegisterView.as_view(), name="register"),
    path("auth/token/", views.CustomTokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("auth/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),

    # Dados de referência
    path("clubs/", views.ClubListView.as_view(), name="club-list"),
    path("leagues/", views.LeagueListView.as_view(), name="league-list"),
    path("competitions/", views.CompetitionListView.as_view(), name="competition-list"),

    # Jogador
    path("player/", views.PlayerView.as_view(), name="player"),
    path("player/stats/", views.PlayerStatsView.as_view(), name="player-stats"),
    path("player/train/", views.PlayerTrainView.as_view(), name="player-train"),

    # Carreira
    path("career/", views.CareerView.as_view(), name="career"),
    path("achievements/", views.AchievementListView.as_view(), name="achievement-list"),

    # Partidas
    path("matches/", views.MatchListView.as_view(), name="match-list"),
    path("matches/simulate/", views.SimulateMatchView.as_view(), name="match-simulate"),

    # Contratos e lesões
    path("contracts/", views.ContractListView.as_view(), name="contract-list"),
    path("injuries/", views.InjuryListView.as_view(), name="injury-list"),

    # Transferências
    path("transfers/", views.TransferListView.as_view(), name="transfer-list"),
    path("transfers/generate/", views.TransferGenerateView.as_view(), name="transfer-generate"),
    path("transfers/<int:pk>/accept/", views.TransferAcceptView.as_view(), name="transfer-accept"),
    path("transfers/<int:pk>/reject/", views.TransferRejectView.as_view(), name="transfer-reject"),
    path("transfers/<int:pk>/negotiate/", views.TransferNegotiateView.as_view(), name="transfer-negotiate"),

    # Decisões
    path("decisions/", views.DecisionEventListView.as_view(), name="decision-list"),
    path("decisions/submit/", views.DecisionSubmitView.as_view(), name="decision-submit"),
]
