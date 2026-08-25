"""
Regras de evolução de atributos via treinamento.

Mantido separado do model para deixar claro que ganhos de evolução são uma
regra de jogo (podem mudar/balancear) e não uma característica estrutural
dos dados.
"""
import random

# Cada tipo de treino afeta um conjunto de atributos. Os ganhos são pequenos
# de propósito para evitar evolução exagerada (item 11 do briefing).
TREINOS = {
    "finalizacao": {"principal": ["finalizacao"], "secundario": ["posicionamento"], "energia": 15},
    "fisico": {"principal": ["forca", "fisico"], "secundario": [], "energia": 20},
    "velocidade": {"principal": ["velocidade", "aceleracao"], "secundario": [], "energia": 15},
    "passe": {"principal": ["passe"], "secundario": ["inteligencia"], "energia": 12},
    "drible": {"principal": ["drible"], "secundario": ["aceleracao"], "energia": 15},
    "defensivo": {"principal": ["defesa"], "secundario": ["posicionamento"], "energia": 15},
}

# Jogadores mais jovens evoluem mais rápido; acima dos 30 a evolução cai bastante.
def _fator_idade(idade: int) -> float:
    if idade <= 20:
        return 1.3
    if idade <= 25:
        return 1.0
    if idade <= 30:
        return 0.7
    if idade <= 34:
        return 0.35
    return 0.1


def calcular_ganhos_treino(tipo_treino: str, idade: int, seed: int | None = None) -> dict:
    """Retorna um dicionário {atributo: pontos_ganhos} para um treino."""
    config = TREINOS.get(tipo_treino)
    if not config:
        return {}

    rng = random.Random(seed)
    fator = _fator_idade(idade)
    ganhos = {}

    for atributo in config["principal"]:
        base = rng.randint(1, 3)
        ganhos[atributo] = ganhos.get(atributo, 0) + max(0, round(base * fator))

    for atributo in config["secundario"]:
        base = rng.randint(0, 1)
        if base:
            ganhos[atributo] = ganhos.get(atributo, 0) + max(0, round(base * fator))

    return ganhos


def custo_energia(tipo_treino: str) -> int:
    config = TREINOS.get(tipo_treino, {})
    return config.get("energia", 15)
