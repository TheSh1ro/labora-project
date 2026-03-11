import type { ToolCallInfo } from '@/types';
import { Wrench, Check, X, ChevronDown, ChevronUp } from 'lucide-react';
import { cn } from '@/lib/utils';
import { useState } from 'react';

interface ToolCallProps {
  toolCalls: ToolCallInfo[];
}

export function ToolCallDisplay({ toolCalls }: ToolCallProps) {
  const [expandedIndex, setExpandedIndex] = useState<number | null>(null);

  if (!toolCalls || toolCalls.length === 0) return null;

  const getToolIcon = (name: string) => {
    if (name.includes('search')) return '🔍';
    if (name.includes('calculate')) return '🧮';
    if (name.includes('get_')) return '📋';
    return '🔧';
  };

  const getToolLabel = (name: string) => {
    const labels: Record<string, string> = {
      search_labor_law: 'Pesquisar Código do Trabalho',
      search_irs_tables: 'Consultar Tabelas IRS',
      search_social_security: 'Pesquisar Segurança Social',
      calculate_vacation_subsidy: 'Calcular Subsídio de Férias',
      calculate_christmas_subsidy: 'Calcular Subsídio de Natal',
      get_minimum_wage: 'Obter Salário Mínimo',
      calculate_tsu: 'Calcular TSU',
    };
    return labels[name] || name;
  };

  return (
    <div className="mt-4 space-y-2">
      <div className="flex items-center gap-2 text-xs text-slate-400 mb-3">
        <Wrench size={12} />
        <span>Tools executadas ({toolCalls.length})</span>
      </div>

      <div className="space-y-2.5">
        {toolCalls.map((tool, index) => {
          const isExpanded = expandedIndex === index;
          const hasError = !!tool.error;
          const hasArguments =
            tool.arguments && Object.keys(tool.arguments).length > 0;

          return (
            <div
              key={index}
              className={cn(
                'bg-slate-800/50 border rounded-lg overflow-hidden transition-all duration-200',
                hasError
                  ? 'border-red-500/30'
                  : 'border-slate-700/50 hover:border-slate-600'
              )}
            >
              <button
                onClick={() => setExpandedIndex(isExpanded ? null : index)}
                className="w-full flex items-center justify-between p-3 text-left"
              >
                <div className="flex items-center gap-2">
                  <span className="text-sm">{getToolIcon(tool.name)}</span>
                  <span className="text-xs font-medium text-slate-300">
                    {getToolLabel(tool.name)}
                  </span>
                  {hasError ? (
                    <X size={12} className="text-red-400" />
                  ) : (
                    <Check size={12} className="text-emerald-400" />
                  )}
                </div>
                {isExpanded ? (
                  <ChevronUp size={14} className="text-slate-500" />
                ) : (
                  <ChevronDown size={14} className="text-slate-500" />
                )}
              </button>

              {isExpanded && (
                <div className="px-3 pb-4 pt-2 border-t border-slate-700/50">
                  <div className="space-y-3">
                    {hasArguments && (
                      <div>
                        <span className="text-[10px] uppercase tracking-wider text-slate-500">
                          Argumentos
                        </span>
                        <pre className="mt-1 text-xs bg-slate-900/50 p-2 rounded text-slate-300 overflow-x-auto">
                          {JSON.stringify(tool.arguments, null, 2)}
                        </pre>
                      </div>
                    )}

                    {tool.result && (
                      <div>
                        <span className="text-[10px] uppercase tracking-wider text-slate-500">
                          Resultado
                        </span>
                        <pre className="mt-1 text-xs bg-slate-900/50 p-2 rounded text-emerald-300 overflow-x-auto max-h-32 overflow-y-auto">
                          {tool.result.length > 300
                            ? tool.result.substring(0, 300) + '...'
                            : tool.result}
                        </pre>
                      </div>
                    )}

                    {tool.error && (
                      <div>
                        <span className="text-[10px] uppercase tracking-wider text-slate-500">
                          Erro
                        </span>
                        <pre className="mt-1 text-xs bg-red-900/20 p-2 rounded text-red-300 overflow-x-auto">
                          {tool.error}
                        </pre>
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
