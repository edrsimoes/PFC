import { GameProvider, useGame } from './context/GameContext';

function ConteudoJogo() {
  const { telaAtual, jogador } = useGame();

  return (
    <div className="min-h-screen bg-slate-900 text-white flex flex-col items-center justify-center p-4">
      <header className="mb-8 text-center">
        <h1 className="text-4xl font-extrabold tracking-wider text-emerald-400">FutCarreira</h1>
        <p className="text-slate-400 text-sm">Simulador de Carreira de Jogador</p>
      </header>

      <main className="w-full max-w-2xl bg-slate-800 border border-slate-700 rounded-xl p-6 shadow-2xl">
        {telaAtual === 'criacao' && (
          <div className="text-center">
            <h2 className="text-xl font-bold mb-4 text-emerald-400">Criar Novo Jogador</h2>
            <p className="text-slate-300">Ambiente pronto! Vamos construir o formulário de criação agora.</p>
          </div>
        )}

        {telaAtual === 'dashboard' && (
          <div>
            <h2 className="text-2xl font-bold text-emerald-400">{jogador.nome}</h2>
            <p className="text-slate-400">{jogador.posicao} | {jogador.clubeAtual}</p>
          </div>
        )}
      </main>
    </div>
  );
}

export default function App() {
  return (
    <GameProvider>
      <ConteudoJogo />
    </GameProvider>
  );
}