import { useState } from 'react';
import type { EvaluationSummary, EvaluationCase } from '@/types';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import {
  BarChart3,
  Play,
  CheckCircle,
  XCircle,
  Clock,
  BookOpen,
  ChevronDown,
  ChevronUp,
  Loader2,
  Download,
} from 'lucide-react';
import { cn } from '@/lib/utils';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const CATEGORY_COLORS: Record<string, string> = {
  'básico': 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30',
  'intermédio': 'bg-blue-500/20 text-blue-400 border-blue-500/30',
  'avançado': 'bg-amber-500/20 text-amber-400 border-amber-500/30',
  'limite': 'bg-purple-500/20 text-purple-400 border-purple-500/30',
};

export function EvaluationDashboard() {
  const [results, setResults] = useState<EvaluationSummary | null>(null);
  const [cases, setCases] = useState<EvaluationCase[]>([]);
  const [isRunning, setIsRunning] = useState(false);
  const [expandedCase, setExpandedCase] = useState<string | null>(null);
  const [hasLoaded, setHasLoaded] = useState(false);

  const loadCases = async () => {
    try {
      const response = await fetch(`${API_URL}/evaluation/cases`);
      if (response.ok) {
        const data = await response.json();
        setCases(data);
      }
    } catch (error) {
      console.error('Erro ao carregar casos:', error);
    }
  };

  const runEvaluation = async () => {
    setIsRunning(true);
    try {
      const response = await fetch(`${API_URL}/evaluation/run`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
      });
      if (response.ok) {
        const data = await response.json();
        setResults(data);
      }
    } catch (error) {
      console.error('Erro ao executar avaliação:', error);
    } finally {
      setIsRunning(false);
    }
  };

  const exportResults = () => {
    if (!results) return;
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19);
    const filename = `evaluation_${timestamp}.json`;
    const blob = new Blob([JSON.stringify(results, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.click();
    URL.revokeObjectURL(url);
  };

  // Carrega casos na primeira renderização
  if (!hasLoaded) {
    loadCases();
    setHasLoaded(true);
  }

  const getScoreColor = (score: number) => {
    if (score >= 0.8) return 'text-emerald-400';
    if (score >= 0.6) return 'text-amber-400';
    return 'text-red-400';
  };

  return (
    <div className="h-full bg-slate-950 p-4 overflow-auto">
      <div className="max-w-6xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-emerald-600 to-emerald-800 flex items-center justify-center">
              <BarChart3 size={20} className="text-white" />
            </div>
            <div>
              <h1 className="text-lg font-semibold text-slate-100">
                Suite de Avaliação
              </h1>
              <p className="text-xs text-slate-400">
                {cases.length} casos de teste definidos
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            {results && (
              <Button
                onClick={exportResults}
                variant="outline"
                className="border-slate-700 text-slate-300 hover:bg-slate-800 hover:text-slate-100"
              >
                <Download size={16} className="mr-2" />
                Exportar JSON
              </Button>
            )}
            <Button
              onClick={runEvaluation}
              disabled={isRunning}
              className={cn(
                'bg-emerald-600 hover:bg-emerald-700 text-white',
                'disabled:opacity-50 disabled:cursor-not-allowed'
              )}
            >
              {isRunning ? (
                <>
                  <Loader2 size={16} className="mr-2 animate-spin" />
                  Executando...
                </>
              ) : (
                <>
                  <Play size={16} className="mr-2" />
                  Executar Avaliação
                </>
              )}
            </Button>
          </div>
        </div>

        {/* Results Summary */}
        {results && (
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <Card className="bg-slate-900 border-slate-800">
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-xs text-slate-400">Corretude</p>
                    <p className={cn('text-2xl font-bold', getScoreColor(results.avg_correctness))}>
                      {(results.avg_correctness * 100).toFixed(0)}%
                    </p>
                  </div>
                  <CheckCircle size={24} className="text-slate-600" />
                </div>
                <Progress
                  value={results.avg_correctness * 100}
                  className="mt-2 h-1.5"
                />
              </CardContent>
            </Card>

            <Card className="bg-slate-900 border-slate-800">
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-xs text-slate-400">Citações</p>
                    <p className={cn('text-2xl font-bold', getScoreColor(results.avg_citation))}>
                      {(results.avg_citation * 100).toFixed(0)}%
                    </p>
                  </div>
                  <BookOpen size={24} className="text-slate-600" />
                </div>
                <Progress
                  value={results.avg_citation * 100}
                  className="mt-2 h-1.5"
                />
              </CardContent>
            </Card>

            <Card className="bg-slate-900 border-slate-800">
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-xs text-slate-400">Recusa Graciosa</p>
                    <p className={cn('text-2xl font-bold', getScoreColor(results.avg_refusal))}>
                      {(results.avg_refusal * 100).toFixed(0)}%
                    </p>
                  </div>
                  <XCircle size={24} className="text-slate-600" />
                </div>
                <Progress
                  value={results.avg_refusal * 100}
                  className="mt-2 h-1.5"
                />
              </CardContent>
            </Card>

            <Card className="bg-slate-900 border-slate-800">
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-xs text-slate-400">Tempo Médio</p>
                    <p className="text-2xl font-bold text-blue-400">
                      {results.avg_response_time_ms.toFixed(0)}ms
                    </p>
                  </div>
                  <Clock size={24} className="text-slate-600" />
                </div>
                <Progress
                  value={Math.min(results.avg_response_time_ms / 100, 100)}
                  className="mt-2 h-1.5"
                />
              </CardContent>
            </Card>
          </div>
        )}

        {/* Results by Category */}
        {results && results.results_by_category && (
          <Card className="bg-slate-900 border-slate-800">
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium text-slate-200">
                Resultados por Categoria
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                {Object.entries(results.results_by_category).map(([category, data]) => (
                  <div
                    key={category}
                    className={cn(
                      'p-3 rounded-lg border',
                      CATEGORY_COLORS[category] || 'bg-slate-800 text-slate-300 border-slate-700'
                    )}
                  >
                    <p className="text-xs font-medium capitalize">{category}</p>
                    <p className="text-lg font-bold mt-1">
                      {(data.avg_correctness * 100).toFixed(0)}%
                    </p>
                    <p className="text-[10px] opacity-70">{data.count} casos</p>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}

        {/* Detailed Results */}
        {results && results.detailed_results && (
          <Card className="bg-slate-900 border-slate-800">
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium text-slate-200">
                Resultados Detalhados
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              {results.detailed_results.map((result, index) => {
                const isExpanded = expandedCase === result.case.id;

                return (
                  <div
                    key={result.case.id}
                    className={cn(
                      'border rounded-lg overflow-hidden transition-all duration-200',
                      isExpanded
                        ? 'border-slate-600 bg-slate-800/50'
                        : 'border-slate-800 bg-slate-800/30 hover:border-slate-700'
                    )}
                  >
                    <button
                      onClick={() => setExpandedCase(isExpanded ? null : result.case.id)}
                      className="w-full flex items-center justify-between p-3 text-left"
                    >
                      <div className="flex items-center gap-3">
                        <span className="text-xs text-slate-500">#{index + 1}</span>
                        <Badge
                          variant="outline"
                          className={cn(
                            'text-[10px] capitalize',
                            CATEGORY_COLORS[result.case.category]
                          )}
                        >
                          {result.case.category}
                        </Badge>
                        <span className="text-sm text-slate-300 truncate max-w-md">
                          {result.case.question}
                        </span>
                      </div>
                      <div className="flex items-center gap-3">
                        <div className="flex items-center gap-1">
                          <CheckCircle size={12} className="text-slate-500" />
                          <span
                            className={cn(
                              'text-xs',
                              getScoreColor(result.correctness_score)
                            )}
                          >
                            {(result.correctness_score * 100).toFixed(0)}%
                          </span>
                        </div>
                        {isExpanded ? (
                          <ChevronUp size={14} className="text-slate-500" />
                        ) : (
                          <ChevronDown size={14} className="text-slate-500" />
                        )}
                      </div>
                    </button>

                    {isExpanded && (
                      <div className="px-4 pb-4 pt-2 border-t border-slate-700/50 space-y-3">
                        <div>
                          <p className="text-[10px] uppercase tracking-wider text-slate-500 mb-1">
                            Resposta
                          </p>
                          <div className="bg-slate-900 p-3 rounded text-sm text-slate-300 max-h-48 overflow-y-auto">
                            {result.response}
                          </div>
                        </div>

                        <div className="grid grid-cols-3 gap-4">
                          <div>
                            <p className="text-[10px] uppercase tracking-wider text-slate-500 mb-1">
                              Corretude
                            </p>
                            <Progress
                              value={result.correctness_score * 100}
                              className="h-1.5"
                            />
                            <p
                              className={cn(
                                'text-xs mt-1',
                                getScoreColor(result.correctness_score)
                              )}
                            >
                              {(result.correctness_score * 100).toFixed(0)}%
                            </p>
                          </div>
                          <div>
                            <p className="text-[10px] uppercase tracking-wider text-slate-500 mb-1">
                              Citações
                            </p>
                            <Progress
                              value={result.citation_score * 100}
                              className="h-1.5"
                            />
                            <p
                              className={cn(
                                'text-xs mt-1',
                                getScoreColor(result.citation_score)
                              )}
                            >
                              {(result.citation_score * 100).toFixed(0)}%
                            </p>
                          </div>
                          <div>
                            <p className="text-[10px] uppercase tracking-wider text-slate-500 mb-1">
                              Tempo
                            </p>
                            <p className="text-xs text-slate-300 mt-1">
                              {result.response_time_ms.toFixed(0)}ms
                            </p>
                          </div>
                        </div>

                        {result.sources.length > 0 && (
                          <div>
                            <p className="text-[10px] uppercase tracking-wider text-slate-500 mb-1">
                              Fontes ({result.sources.length})
                            </p>
                            <div className="flex flex-wrap gap-2">
                              {result.sources.map((source, idx) => (
                                <a
                                  key={idx}
                                  href={source.url}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  className="text-xs text-blue-400 hover:text-blue-300 underline"
                                >
                                  {source.title}
                                </a>
                              ))}
                            </div>
                          </div>
                        )}

                        {result.tool_calls.length > 0 && (
                          <div>
                            <p className="text-[10px] uppercase tracking-wider text-slate-500 mb-1">
                              Tools ({result.tool_calls.length})
                            </p>
                            <div className="flex flex-wrap gap-2">
                              {result.tool_calls.map((tool, idx) => (
                                <span
                                  key={idx}
                                  className="text-xs bg-slate-900 px-2 py-1 rounded text-slate-400"
                                >
                                  {tool.name}
                                </span>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                );
              })}
            </CardContent>
          </Card>
        )}

        {/* Test Cases List */}
        {!results && cases.length > 0 && (
          <Card className="bg-slate-900 border-slate-800">
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium text-slate-200">
                Casos de Teste Disponíveis
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                {cases.map((testCase, index) => (
                  <div
                    key={testCase.id}
                    className="flex items-center gap-3 p-3 bg-slate-800/50 rounded-lg border border-slate-800"
                  >
                    <span className="text-xs text-slate-500">#{index + 1}</span>
                    <Badge
                      variant="outline"
                      className={cn(
                        'text-[10px] capitalize',
                        CATEGORY_COLORS[testCase.category]
                      )}
                    >
                      {testCase.category}
                    </Badge>
                    <span className="text-sm text-slate-300 flex-1">
                      {testCase.question}
                    </span>
                    {testCase.requires_calculation && (
                      <span className="text-[10px] bg-amber-500/20 text-amber-400 px-2 py-0.5 rounded">
                        Cálculo
                      </span>
                    )}
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}