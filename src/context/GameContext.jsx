import { createContext, useState, useContext } from 'react';

const GameContext = createContext();

export function GameProvider({ children }) {
  const [telaAtual, setTelaAtual] = useState('criacao');
  const [jogador, setJogador] = useState({
    nome: '',
    nacionalidade: 'Brasil',
    posicao: 'Atacante',
    idade: 18,
    overall: 65,
    clubeAtual: '',
    titulos: [],
    estatisticasGerais: { jogos: 0, gols: 0, assistencias: 0 },
    historicoClubes: []
  });

  const iniciarCarreira = (dadosIniciais) => {
    setJogador((prev) => ({
      ...prev,
      ...dadosIniciais,
      historicoClubes: [
        {
          clube: dadosIniciais.clubeAtual,
          anoInicio: 2026,
          anoFim: null,
          jogos: 0,
          gols: 0,
          assistencias: 0
        }
      ]
    }));
    setTelaAtual('dashboard');
  };

  return (
    <GameContext.Provider value={{ jogador, setJogador, telaAtual, setTelaAtual, iniciarCarreira }}>
      {children}
    </GameContext.Provider>
  );
}

export function useGame() {
  return useContext(GameContext);
}