import { useState, useEffect } from 'react';
import { Chat } from '@/components/Chat';
import { EvaluationDashboard } from '@/components/EvaluationDashboard';
import { Button } from '@/components/ui/button';
import { MessageSquare, BarChart3, Github, BookOpen, Coins } from 'lucide-react';
import { cn } from '@/lib/utils';
import { useChat } from '@/hooks/useChat';

type Tab = 'chat' | 'evaluation';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

interface AgentInfo {
  model: string;
  provider: string;
  display_name: string;
  tool_calling: boolean;
}

function App() {
  const [activeTab, setActiveTab] = useState<Tab>('chat');
  const [agentInfo, setAgentInfo] = useState<AgentInfo | null>(null);
  const chatHook = useChat();
  const { sessionUsage } = chatHook;
  // const hasUsage = sessionUsage.total_tokens > 0;

  useEffect(() => {
    fetch(`${API_URL}/agent/info`)
      .then(res => res.json())
      .then(data => setAgentInfo(data))
      .catch(() => null);
  }, []);

  return (
    <div className="h-screen bg-slate-950 flex flex-col">
      {/* Navigation */}
      <nav className="flex items-center justify-between px-4 py-2 bg-slate-900 border-b border-slate-800">
        <div className="flex items-center gap-6">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-blue-600 to-blue-800 flex items-center justify-center">
              <BookOpen size={16} className="text-white" />
            </div>
            <span className="text-sm font-semibold text-slate-100">
              HomoDeus Challenge
            </span>
          </div>

          <div className="flex items-center gap-1">
            <button
              onClick={() => setActiveTab('chat')}
              className={cn(
                'flex items-center gap-2 px-3 py-1.5 rounded-md text-sm transition-all duration-200',
                activeTab === 'chat'
                  ? 'bg-blue-600/20 text-blue-400'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800'
              )}
            >
              <MessageSquare size={14} />
              Chat
            </button>
            <button
              onClick={() => setActiveTab('evaluation')}
              className={cn(
                'flex items-center gap-2 px-3 py-1.5 rounded-md text-sm transition-all duration-200',
                activeTab === 'evaluation'
                  ? 'bg-emerald-600/20 text-emerald-400'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800'
              )}
            >
              <BarChart3 size={14} />
              Avaliação
            </button>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <div
            className={cn(
              'flex items-center gap-2 px-3 py-1.5 rounded-md',
              'border border-slate-700 bg-slate-800/60',
              'transition-opacity duration-300',
              // hasUsage ? 'opacity-100' : 'opacity-40'
            )}
          >
            <Coins size={12} className="text-amber-400 flex-shrink-0" />
            <div className="flex items-center gap-2 text-[10px]">
              <span className="text-slate-400">
                <span className="text-slate-200 font-medium tabular-nums">
                  {sessionUsage.total_tokens.toLocaleString()}
                </span>
                {' '}tokens
              </span>
              <span className="text-slate-600">·</span>
              <span className="text-amber-400 font-medium tabular-nums">
                ${sessionUsage.estimated_cost_usd.toFixed(4)}
              </span>
            </div>
          </div>

          <Button
            variant="ghost"
            size="sm"
            onClick={() => window.open('https://github.com', '_blank')}
            className="text-slate-400 hover:text-slate-200"
          >
            <Github size={16} className="mr-1" />
            GitHub
          </Button>
        </div>
      </nav>

      {/* Main Content — passa o hook ao Chat para partilhar estado */}
      <main className="flex-1 overflow-hidden">
        {activeTab === 'chat'
          ? <Chat chatHook={chatHook} />
          : <EvaluationDashboard />
        }
      </main>

      {/* Footer */}
      <footer className="px-4 py-2 bg-slate-900 border-t border-slate-800">
        <div className="flex items-center justify-between text-[10px] text-slate-500">
          <div className="flex items-center gap-4">
            <span>Agente Q&A de Direito Laboral Português</span>
            <span>•</span>
            <span>HomoDeus Challenge 2025</span>
          </div>
          <div className="flex items-center gap-4">
            {agentInfo ? (
              <>
                <span>{agentInfo.provider} · {agentInfo.display_name}</span>
                <span>•</span>
              </>
            ) : null}
            <span>Tool Calling</span>
            <span>•</span>
            <span>Tavily Search</span>
          </div>
        </div>
      </footer>
    </div>
  );
}

export default App;