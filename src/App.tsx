import { useState, useEffect } from 'react';
import { Chat } from '@/components/Chat';
import { EvaluationDashboard } from '@/components/EvaluationDashboard';
import {
  MessageSquare,
  BarChart3,
  Github,
  BookOpen,
  Coins,
  ChevronLeft,
  Gavel,
  CirclePlus,
  Database,
} from 'lucide-react';
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

interface AgentUsage {
  prompt_tokens: number;
  completion_tokens: number;
  total_tokens: number;
  estimated_cost_usd: number;
}

function App() {
  const [activeTab, setActiveTab] = useState<Tab>('chat');
  const [agentInfo, setAgentInfo] = useState<AgentInfo | null>(null);
  const [agentUsage, setAgentUsage] = useState<AgentUsage | null>(null);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const chatHook = useChat();
  const { sessionUsage, clearChat } = chatHook;

  useEffect(() => {
    fetch(`${API_URL}/agent/info`)
      .then((res) => res.json())
      .then((data) => setAgentInfo(data))
      .catch(() => null);
  }, []);

  useEffect(() => {
    const fetchUsage = () => {
      fetch(`${API_URL}/agent/usage`)
        .then((res) => res.json())
        .then((data) => setAgentUsage(data))
        .catch(() => null);
    };
    fetchUsage();
    const interval = setInterval(fetchUsage, 10000);
    return () => clearInterval(interval);
  }, []);

  const handleNewConversation = async () => {
    clearChat();
    try {
      await fetch(`${API_URL}/session`, { method: 'DELETE' });
    } catch {
      // silencia erros de rede — estado local já foi limpo
    }
    setActiveTab('chat');
  };

  return (
    <div className="h-screen bg-slate-950 flex overflow-hidden">
      {/* Sidebar */}
      <aside
        className={cn(
          'flex flex-col bg-slate-900 border-r border-slate-800 transition-all duration-300 ease-in-out flex-shrink-0',
          sidebarCollapsed ? 'w-[60px]' : 'w-[220px]'
        )}
      >
        {/* Logo */}
        <div
          className={cn(
            'flex items-center gap-3 px-3 py-4 border-b border-slate-800 min-h-[74px]'
          )}
        >
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-blue-600 to-blue-800 flex items-center justify-center flex-shrink-0 shadow-lg shadow-blue-900/30">
            <Gavel size={15} className="text-white" />
          </div>
          {!sidebarCollapsed && (
            <div className="overflow-hidden">
              <span className="text-sm font-semibold text-slate-100 block leading-tight whitespace-nowrap">
                AI Engineer
              </span>
              <span className="text-[10px] text-slate-500 whitespace-nowrap">
                Challenge 2025
              </span>
            </div>
          )}
        </div>

        {/* Nav Items */}
        <nav className="flex-1 p-2 space-y-1 pt-3">
          {/* Nova Conversa */}
          <button
            onClick={handleNewConversation}
            className={cn(
              'w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-all duration-200 min-h-11',
              'text-slate-400 hover:text-slate-200 hover:bg-slate-800 border border-dashed border-slate-700 hover:border-slate-500'
            )}
            title={sidebarCollapsed ? 'Nova conversa' : undefined}
          >
            <CirclePlus size={16} className="flex-shrink-0" />
            {!sidebarCollapsed && (
              <span className="whitespace-nowrap">Nova conversa</span>
            )}
          </button>

          <button
            onClick={() => setActiveTab('chat')}
            className={cn(
              'w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-all duration-200 group min-h-11',
              activeTab === 'chat'
                ? 'bg-blue-600/15 text-blue-400 border border-blue-500/20'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800'
            )}
            title={sidebarCollapsed ? 'Chat' : undefined}
          >
            <MessageSquare size={16} className="flex-shrink-0" />
            {!sidebarCollapsed && <span>Chat</span>}
          </button>

          <button
            onClick={() => setActiveTab('evaluation')}
            className={cn(
              'w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-all duration-200 group min-h-11',
              activeTab === 'evaluation'
                ? 'bg-emerald-600/15 text-emerald-400 border border-emerald-500/20'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800'
            )}
            title={sidebarCollapsed ? 'Avaliação' : undefined}
          >
            <BarChart3 size={16} className="flex-shrink-0" />
            {!sidebarCollapsed && <span>Desempenho</span>}
          </button>
        </nav>

        {/* Bottom section */}
        <div className="p-2 border-t border-slate-800 space-y-1.5">
          {/* Total Agent Usage */}
          <div
            className={cn(
              'rounded-lg bg-blue-950/30 border border-blue-800/30 transition-all',
              sidebarCollapsed
                ? 'flex items-center justify-center px-2 py-3'
                : 'px-3 py-3'
            )}
            title={
              sidebarCollapsed && agentUsage
                ? `Total: ${agentUsage.total_tokens.toLocaleString()} tokens · $${agentUsage.estimated_cost_usd.toFixed(4)}`
                : undefined
            }
          >
            {sidebarCollapsed ? (
              <Database size={13} className="text-blue-400" />
            ) : (
              <div className="flex flex-col gap-1 min-w-0">
                <div className="flex items-center gap-1.5">
                  <Database size={11} className="text-blue-400 flex-shrink-0" />
                  <span className="text-[10px] text-slate-500 uppercase tracking-wider font-medium whitespace-nowrap">
                    Total tokens
                  </span>
                </div>
                <span className="text-slate-100 font-semibold tabular-nums text-base leading-none truncate">
                  {agentUsage ? agentUsage.total_tokens.toLocaleString() : '—'}
                </span>
                <span className="text-blue-400 font-medium tabular-nums text-xs leading-none">
                  {agentUsage
                    ? `$${agentUsage.estimated_cost_usd.toFixed(4)}`
                    : '—'}
                </span>
              </div>
            )}
          </div>

          {/* Session Token Usage */}
          <div
            className={cn(
              'rounded-lg bg-slate-800/20 border border-slate-700/50 transition-all',
              sidebarCollapsed
                ? 'flex items-center justify-center px-2 py-3'
                : 'px-3 py-3'
            )}
            title={
              sidebarCollapsed
                ? `${sessionUsage.total_tokens.toLocaleString()} tokens · $${sessionUsage.estimated_cost_usd.toFixed(4)}`
                : undefined
            }
          >
            {sidebarCollapsed ? (
              <Coins size={13} className="text-amber-400" />
            ) : (
              <div className="flex flex-col gap-1 min-w-0">
                <div className="flex items-center gap-1.5">
                  <Coins size={11} className="text-amber-400 flex-shrink-0" />
                  <span className="text-[10px] text-slate-500 uppercase tracking-wider font-medium whitespace-nowrap">
                    Chat tokens
                  </span>
                </div>
                <span className="text-slate-100 font-semibold tabular-nums text-base leading-none truncate">
                  {sessionUsage.total_tokens.toLocaleString()}
                </span>
                <span className="text-amber-400 font-medium tabular-nums text-xs leading-none">
                  ${sessionUsage.estimated_cost_usd.toFixed(4)}
                </span>
              </div>
            )}
          </div>

          {/* GitHub */}
          <button
            onClick={() => window.open('https://github.com', '_blank')}
            className={cn(
              'w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm text-slate-400 hover:text-slate-200 hover:bg-slate-800 transition-all duration-200 min-h-11'
            )}
            title={sidebarCollapsed ? 'GitHub' : undefined}
          >
            <Github size={15} className="flex-shrink-0" />
            {!sidebarCollapsed && <span>GitHub</span>}
          </button>

          {/* Collapse toggle */}
          <button
            onClick={() => setSidebarCollapsed((v) => !v)}
            className="w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm text-slate-500 hover:text-slate-300 hover:bg-slate-800 transition-all duration-200 min-h-11"
          >
            <ChevronLeft
              size={14}
              className={cn(
                'flex-shrink-0 transition-transform duration-300',
                sidebarCollapsed && 'rotate-180'
              )}
            />
            <span
              className={cn(
                'overflow-hidden whitespace-nowrap transition-all duration-300',
                sidebarCollapsed ? 'w-0 opacity-0' : 'w-auto opacity-100'
              )}
            >
              Recolher
            </span>
          </button>
        </div>
      </aside>

      {/* Main Content */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        {/* Top bar — minimal, just agent info */}
        <header className="flex items-center justify-between px-5 py-2.5 bg-slate-900/60 border-b border-slate-800 backdrop-blur-sm flex-shrink-0">
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
            <span className="text-xs text-slate-400">
              {activeTab === 'chat'
                ? 'Agente Q&A · Direito Laboral Português'
                : 'Painel de testes'}
            </span>
          </div>
          {agentInfo && (
            <div className="flex items-center gap-2 text-[10px] text-slate-500">
              <BookOpen size={10} />
              <span>
                {agentInfo.provider} · {agentInfo.display_name}
              </span>
              <span className="text-slate-700">·</span>
              <span>Tool Calling</span>
              <span className="text-slate-700">·</span>
              <span>Tavily Search</span>
            </div>
          )}
        </header>

        {/* Page Content */}
        <main className="flex-1 overflow-hidden">
          {activeTab === 'chat' ? (
            <Chat chatHook={chatHook} />
          ) : (
            <EvaluationDashboard />
          )}
        </main>
      </div>
    </div>
  );
}

export default App;
