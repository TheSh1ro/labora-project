import { useState, useRef, useEffect } from 'react';
import { Send, Trash2, Sparkles } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { useChat } from '@/hooks/useChat';
import { Message } from '@/components/Message';
import { SourcesPanel } from '@/components/SourcesPanel';
import { ToolCallDisplay } from '@/components/ToolCall';
import { cn } from '@/lib/utils';

const SUGGESTED_QUESTIONS = [
  'Qual é o salário mínimo nacional atual?',
  'A quantos dias de férias tenho direito?',
  'Como se calcula o subsídio de férias?',
  'Quais são as taxas de TSU?',
  'Como funciona o subsídio de Natal?',
];

interface ChatProps {
  chatHook?: ReturnType<typeof useChat>;
}

export function Chat({ chatHook }: ChatProps) {
  const [input, setInput] = useState('');
  const scrollRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const internalHook = useChat();
  const {
    messages,
    isLoading,
    error,
    lastSources,
    lastToolCalls,
    responseTime,
    sendMessage,
    clearChat,
  } = chatHook ?? internalHook;

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, isLoading]);

  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;
    const message = input.trim();
    setInput('');
    await sendMessage(message);
  };

  const handleSuggestedQuestion = (question: string) => {
    setInput(question);
    inputRef.current?.focus();
  };

  const lastAssistantMessage = messages.filter(m => m.role === 'assistant').pop();

  return (
    <div className="flex flex-col h-full bg-slate-950">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-slate-800 bg-slate-900/50">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-blue-600 to-blue-800 flex items-center justify-center">
            <Sparkles size={16} className="text-white" />
          </div>
          <div>
            <h1 className="text-sm font-semibold text-slate-100">
              Agente Direito Laboral PT
            </h1>
            <p className="text-[10px] text-slate-400">
              Especializado em direito laboral português
            </p>
          </div>
        </div>

        {messages.length > 0 && (
          <Button
            variant="ghost"
            size="sm"
            onClick={clearChat}
            className="text-slate-400 hover:text-red-400 hover:bg-red-500/10"
          >
            <Trash2 size={14} className="mr-1" />
            Limpar
          </Button>
        )}
      </div>

      {/* Messages Area */}
      <div ref={scrollRef} className="flex-1 min-h-0 overflow-y-auto px-4">
        {messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full py-12">
            <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-blue-600 to-blue-800 flex items-center justify-center mb-6 shadow-lg shadow-blue-900/20">
              <Sparkles size={28} className="text-white" />
            </div>
            <h2 className="text-xl font-semibold text-slate-100 mb-2">
              Olá! Sou o Agente de Direito Laboral
            </h2>
            <p className="text-sm text-slate-400 text-center max-w-md mb-8">
              Posso ajudar com questões sobre o Código do Trabalho, processamento
              salarial, IRS, TSU, férias e subsídios em Portugal.
            </p>
            <div className="w-full max-w-lg">
              <p className="text-xs text-slate-500 mb-3 text-center">Perguntas sugeridas:</p>
              <div className="flex flex-wrap justify-center gap-2">
                {SUGGESTED_QUESTIONS.map((question, index) => (
                  <button
                    key={index}
                    onClick={() => handleSuggestedQuestion(question)}
                    className={cn(
                      'px-3 py-1.5 text-xs rounded-full',
                      'bg-slate-800 text-slate-300 border border-slate-700',
                      'hover:bg-slate-700 hover:border-slate-600 hover:text-slate-200',
                      'transition-all duration-200'
                    )}
                  >
                    {question}
                  </button>
                ))}
              </div>
            </div>
          </div>
        ) : (
          <div className="py-4 space-y-2">
            {messages.map((message, index) => (
              <Message key={index} message={message} />
            ))}

            {isLoading && (
              <div className="flex gap-3 p-4 animate-in fade-in">
                <div className="w-8 h-8 rounded-full bg-slate-700 flex items-center justify-center">
                  <Sparkles size={14} className="text-slate-300" />
                </div>
                <div className="bg-slate-800 rounded-2xl rounded-bl-md px-4 py-3 flex items-center gap-1">
                  <span className="w-1.5 h-1.5 bg-slate-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                  <span className="w-1.5 h-1.5 bg-slate-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                  <span className="w-1.5 h-1.5 bg-slate-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                </div>
              </div>
            )}

            {error && (
              <div className="mx-4 p-3 bg-red-500/10 border border-red-500/30 rounded-lg">
                <p className="text-xs text-red-400">{error}</p>
              </div>
            )}

            {lastAssistantMessage && !isLoading && (
              <div className="ml-14 mr-4">
                <ToolCallDisplay toolCalls={lastToolCalls} />
                <SourcesPanel sources={lastSources} responseTime={responseTime} />
              </div>
            )}
          </div>
        )}
      </div>

      {/* Input Area */}
      <div className="p-4 border-t border-slate-800 bg-slate-900/50">
        <form onSubmit={handleSubmit} className="flex gap-2">
          <Input
            ref={inputRef}
            value={input}
            onChange={e => setInput(e.target.value)}
            placeholder="Digite sua pergunta sobre direito laboral..."
            disabled={isLoading}
            className={cn(
              'flex-1 bg-slate-800 border-slate-700 text-slate-100',
              'placeholder:text-slate-500',
              'focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500',
              'transition-all duration-200'
            )}
          />
          <Button
            type="submit"
            disabled={isLoading || !input.trim()}
            className={cn(
              'bg-blue-600 hover:bg-blue-700 text-white',
              'disabled:opacity-50 disabled:cursor-not-allowed',
              'transition-all duration-200'
            )}
          >
            <Send size={16} />
          </Button>
        </form>
        <p className="text-[10px] text-slate-500 mt-2 text-center">
          As respostas são geradas por IA e devem ser verificadas com as fontes oficiais.
        </p>
      </div>
    </div>
  );
}