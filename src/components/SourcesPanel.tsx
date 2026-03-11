import type { Source } from '@/types';
import { BookOpen, ExternalLink } from 'lucide-react';
import { cn } from '@/lib/utils';

interface SourcesPanelProps {
  sources: Source[];
  responseTime?: number | null;
}

// Remove prefixos e lixo comum que vem do Tavily/pgdlisboa
function cleanTitle(title: string): string {
  return title
    .replace(/^:::?\s*/g, '') // remove ":::" do início
    .replace(/\s*:::\s*$/g, '') // remove ":::" do fim
    .replace(/^-\s+/, '') // remove "- " do início
    .replace(/\s{2,}/g, ' ') // colapsa espaços duplos
    .trim();
}

// Limpa o snippet: remove pipes, barras, markdown de tabela e trunca bem
function cleanSnippet(snippet: string): string {
  return snippet
    .replace(/\|+/g, ' ') // remove pipes de tabelas
    .replace(/#{1,6}\s/g, '') // remove headers markdown
    .replace(/\*{1,2}(.*?)\*{1,2}/g, '$1') // remove bold/italic
    .replace(/\s{2,}/g, ' ') // colapsa espaços
    .replace(/\\n/g, ' ') // remove \n literais
    .trim()
    .slice(0, 160); // limita tamanho
}

// Extrai domínio legível da URL
function getDomain(url: string): string {
  try {
    const { hostname } = new URL(url);
    return hostname.replace(/^www\./, '');
  } catch {
    return url;
  }
}

export function SourcesPanel({ sources, responseTime }: SourcesPanelProps) {
  if (!sources || sources.length === 0) return null;

  const uniqueSources = sources.filter(
    (source, index, self) =>
      index === self.findIndex((s) => s.url === source.url)
  );

  return (
    <div className="mt-4 pt-4 border-t border-slate-700/50">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2 text-xs text-slate-400">
          <BookOpen size={14} />
          <span>Fontes ({uniqueSources.length})</span>
        </div>
        {responseTime && (
          <span className="text-[10px] text-slate-500">
            {responseTime.toFixed(0)}ms
          </span>
        )}
      </div>

      <div className="space-y-2">
        {uniqueSources.map((source, index) => {
          const title = cleanTitle(source.title);
          const snippet = source.snippet ? cleanSnippet(source.snippet) : null;
          const domain = getDomain(source.url);

          return (
            <a
              key={index}
              href={source.url}
              target="_blank"
              rel="noopener noreferrer"
              className={cn(
                'group flex items-start gap-3 p-3 rounded-lg',
                'bg-slate-800/50 border border-slate-700/50',
                'hover:bg-slate-800 hover:border-slate-600',
                'transition-all duration-200'
              )}
            >
              <ExternalLink
                size={12}
                className="mt-1 text-slate-500 group-hover:text-blue-400 transition-colors flex-shrink-0"
              />
              <div className="min-w-0 flex-1">
                <p className="text-xs font-medium text-slate-200 group-hover:text-blue-300 truncate transition-colors leading-snug">
                  {title}
                </p>
                <p className="text-[10px] text-slate-500 mt-0.5">{domain}</p>
                {snippet && (
                  <p className="text-[11px] text-slate-400 mt-1.5 line-clamp-2 leading-relaxed">
                    {snippet}
                  </p>
                )}
              </div>
            </a>
          );
        })}
      </div>
    </div>
  );
}
