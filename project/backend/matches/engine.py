"""
Motor de simulação de partidas do FutCarreira.

Este módulo é a única fonte de verdade para o que acontece em uma partida.
Ele NÃO depende de views ou serializers - recebe um Player e parâmetros
simples, e devolve uma estrutura de dados com o resultado e os eventos
minuto a minuto. Nada disso deve ser recalculado ou confiado a partir do
frontend.
"""
import random
from dataclasses import dataclass, field

# Posições consideradas "ofensivas" para fins de chance de gol/assistência.
POSICOES_ATAQUE = {
    "atacante", "segundo_atacante", "ponta_esquerda", "ponta_direita",
    "meia_atacante",
}
POSICOES_MEIO = {"meia", "volante", "lateral_esquerdo", "lateral_direito"}
POSICOES_DEFESA = {"zagueiro", "goleiro"}

PESO_IMPORTANCIA = {
    "normal": 1.0,
    "classico": 1.1,
    "decisiva": 1.2,
    "final": 1.35,
}


@dataclass
class ResultadoSimulacao:
    gols_time: int
    gols_adversario: int
    gols_jogador: int
    assistencias_jogador: int
    nota_jogador: float
    minutos_jogados: int
    titular: bool
    lesionou: bool
    gravidade_lesao: str | None
    eventos: list = field(default_factory=list)


def _chance_participacao_gol(overall_jogador, posicao, forma_atual):
    """Probabilidade-base do jogador participar de um gol em uma chance criada."""
    base = 0.15
    if posicao in POSICOES_ATAQUE:
        base = 0.42
    elif posicao in POSICOES_MEIO:
        base = 0.22
    elif posicao in POSICOES_DEFESA:
        base = 0.06

    ajuste_overall = (overall_jogador - 65) * 0.004
    ajuste_forma = forma_atual * 0.01
    return max(0.02, min(0.85, base + ajuste_overall + ajuste_forma))


def simulate_match(
    player,
    forca_adversario: int,
    importancia: str = "normal",
    mandante: bool = True,
    seed: int | None = None,
) -> ResultadoSimulacao:
    """
    Simula uma partida para `player` (instância de players.models.Player).

    Considera: overall, forma atual, atributos, condição física, força do
    adversário, importância da partida e um fator aleatório controlado.
    """
    rng = random.Random(seed)

    overall = player.overall
    forma = player.forma_atual
    condicao = player.condicao_fisica
    posicao = player.posicao

    peso_importancia = PESO_IMPORTANCIA.get(importancia, 1.0)

    # Condição física abaixo de 60 penaliza o desempenho do time e do jogador.
    fator_condicao = 1.0 if condicao >= 60 else 0.75 + (condicao / 240)

    forca_time = (overall * 0.6 + 65 * 0.4) * fator_condicao
    vantagem_mando = 4 if mandante else -2

    diferenca = (forca_time + vantagem_mando) - forca_adversario
    diferenca *= peso_importancia

    eventos = []
    gols_time = 0
    gols_adversario = 0
    gols_jogador = 0
    assistencias_jogador = 0

    minutos_chave = sorted(rng.sample(range(3, 90), k=rng.randint(4, 7)))

    for minuto in minutos_chave:
        # Probabilidade de a jogada gerar uma chance clara de gol para o time.
        prob_chance_time = max(0.15, min(0.75, 0.45 + diferenca / 100))
        chance_time = rng.random() < prob_chance_time

        if chance_time:
            prob_gol_jogador = _chance_participacao_gol(overall, posicao, forma)
            papel = rng.random()

            if papel < prob_gol_jogador:
                gols_time += 1
                gols_jogador += 1
                eventos.append({
                    "minuto": minuto, "tipo": "gol",
                    "descricao": f"GOOOOL! {player.nome_exibicao} balança as redes aos {minuto} minutos!",
                })
            elif papel < prob_gol_jogador * 1.6:
                gols_time += 1
                assistencias_jogador += 1
                eventos.append({
                    "minuto": minuto, "tipo": "assistencia",
                    "descricao": f"{player.nome_exibicao} dá um passe preciso e o companheiro marca aos {minuto} minutos!",
                })
            else:
                convertida = rng.random() < 0.42
                if convertida:
                    gols_time += 1
                    eventos.append({
                        "minuto": minuto, "tipo": "chance",
                        "descricao": f"O time aproveita a jogada e marca aos {minuto} minutos.",
                    })
                else:
                    eventos.append({
                        "minuto": minuto, "tipo": "chance",
                        "descricao": f"Chance clara aos {minuto} minutos, mas a bola vai para fora.",
                    })

        # Chance do adversário responder.
        prob_chance_adv = max(0.1, min(0.65, 0.35 - diferenca / 120))
        if rng.random() < prob_chance_adv:
            convertida = rng.random() < 0.38
            if convertida:
                gols_adversario += 1
                eventos.append({
                    "minuto": minuto, "tipo": "chance",
                    "descricao": f"O adversário aproveita um erro e marca aos {minuto} minutos.",
                })

    eventos.sort(key=lambda e: e["minuto"])

    # Lesão: chance baixa, aumenta com condição física ruim e partidas decisivas.
    prob_lesao = 0.02 + (0 if condicao > 40 else 0.03) + (0.01 if peso_importancia > 1.1 else 0)
    lesionou = rng.random() < prob_lesao
    gravidade_lesao = None
    minutos_jogados = 90
    titular = condicao >= 30

    if lesionou:
        gravidade_lesao = rng.choices(
            ["muscular", "entorse", "grave"], weights=[0.6, 0.3, 0.1], k=1
        )[0]
        minutos_jogados = rng.randint(15, 75)
        eventos.append({
            "minuto": minutos_jogados, "tipo": "lesao",
            "descricao": f"{player.nome_exibicao} sente dores e precisa deixar o campo.",
        })

    # Nota do jogador: base 6.0, some/subtrai conforme participação e resultado.
    nota = 6.0 + gols_jogador * 1.1 + assistencias_jogador * 0.7
    nota += 0.3 if gols_time > gols_adversario else (-0.3 if gols_time < gols_adversario else 0)
    nota += (overall - 65) * 0.01
    nota = max(3.0, min(10.0, round(nota, 1)))

    return ResultadoSimulacao(
        gols_time=gols_time,
        gols_adversario=gols_adversario,
        gols_jogador=gols_jogador,
        assistencias_jogador=assistencias_jogador,
        nota_jogador=nota,
        minutos_jogados=minutos_jogados,
        titular=titular,
        lesionou=lesionou,
        gravidade_lesao=gravidade_lesao,
        eventos=eventos,
    )
