import type { Source } from '@/types';
import { BookOpen, ExternalLink } from 'lucide-react';
import { cn } from '@/lib/utils';

interface SourcesPanelProps {
  sources: Source[];
  responseTime?: number | null;
}

export function SourcesPanel({ sources, responseTime }: SourcesPanelProps) {
  if (!sources || sources.length === 0) return null;

  const uniqueSources = sources.filter(
    (source, index, self) =>
      index === self.findIndex(s => s.url === source.url)
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
        {uniqueSources.map((source, index) => (
          <a
            key={index}
            href={source.url}
            target="_blank"
            rel="noopener noreferrer"
            className={cn(
              'group flex items-start gap-2 p-2.5 rounded-lg',
              'bg-slate-800/50 border border-slate-700/50',
              'hover:bg-slate-800 hover:border-slate-600',
              'transition-all duration-200'
            )}
          >
            <ExternalLink
              size={12}
              className="mt-0.5 text-slate-500 group-hover:text-blue-400 transition-colors flex-shrink-0"
            />
            <div className="min-w-0 flex-1">
              <p className="text-xs font-medium text-slate-300 group-hover:text-blue-300 truncate transition-colors">
                {source.title}
              </p>
              {source.snippet && (
                <p className="text-[10px] text-slate-500 mt-0.5 line-clamp-2">
                  {source.snippet}
                </p>
              )}
            </div>
          </a>
        ))}
      </div>
    </div>
  );
}