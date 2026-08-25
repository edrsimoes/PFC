import json
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand

from career.models import Achievement, DecisionEvent, DecisionOption
from clubs.models import Club, Competition, League

DATA_DIR = Path(settings.BASE_DIR).parent / "data"


class Command(BaseCommand):
    help = "Popula o banco com dados iniciais (clubes, ligas, conquistas, eventos de decisão)."

    def handle(self, *args, **options):
        self._seed_clubs()
        self._seed_competitions()
        self._seed_achievements()
        self._seed_decision_events()
        self.stdout.write(self.style.SUCCESS("Dados iniciais carregados com sucesso."))

    def _seed_clubs(self):
        path = DATA_DIR / "clubs.json"
        clubes = json.loads(path.read_text(encoding="utf-8"))
        criados = 0
        for dados in clubes:
            liga, _ = League.objects.get_or_create(
                nome=dados["liga"], pais=dados["pais"],
                defaults={"prestigio": dados["prestigio"]},
            )
            _, created = Club.objects.get_or_create(
                nome=dados["nome"], pais=dados["pais"],
                defaults={
                    "liga": liga,
                    "overall_minimo": dados["overall_minimo"],
                    "orcamento": dados["orcamento"],
                    "prestigio": dados["prestigio"],
                },
            )
            criados += int(created)
        self.stdout.write(f"Clubes: {criados} criados, {len(clubes) - criados} já existiam.")

    def _seed_competitions(self):
        competicoes = [
            {"nome": "Libertadores da América", "tipo": "continental", "continente": "América do Sul", "prestigio": 85},
            {"nome": "UEFA Champions League", "tipo": "continental", "continente": "Europa", "prestigio": 95},
            {"nome": "Copa do Brasil", "tipo": "copa_nacional", "continente": "América do Sul", "prestigio": 60},
            {"nome": "Seleção Nacional", "tipo": "selecao", "continente": "", "prestigio": 90},
        ]
        criados = 0
        for dados in competicoes:
            _, created = Competition.objects.get_or_create(nome=dados["nome"], defaults=dados)
            criados += int(created)
        self.stdout.write(f"Competições: {criados} criadas.")

    def _seed_achievements(self):
        path = DATA_DIR / "achievements.json"
        itens = json.loads(path.read_text(encoding="utf-8"))
        criados = 0
        for dados in itens:
            _, created = Achievement.objects.get_or_create(codigo=dados["codigo"], defaults=dados)
            criados += int(created)
        self.stdout.write(f"Conquistas: {criados} criadas.")

    def _seed_decision_events(self):
        path = DATA_DIR / "events.json"
        eventos = json.loads(path.read_text(encoding="utf-8"))
        criados = 0
        for dados in eventos:
            opcoes = dados.pop("opcoes")
            evento, created = DecisionEvent.objects.get_or_create(
                codigo=dados["codigo"], defaults=dados
            )
            criados += int(created)
            if created:
                for opcao in opcoes:
                    DecisionOption.objects.create(evento=evento, **opcao)
        self.stdout.write(f"Eventos de decisão: {criados} criados.")
