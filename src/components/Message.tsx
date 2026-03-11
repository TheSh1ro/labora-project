import type { Message as MessageType, Source, ToolCallInfo } from '@/types';
import { Bot, User, ClipboardCopy, ClipboardCheck } from 'lucide-react';
import { cn } from '@/lib/utils';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { SourcesPanel } from '@/components/SourcesPanel';
import { ToolCallDisplay } from '@/components/ToolCall';
import { useState } from 'react';

interface MessageProps {
  message: MessageType;
  sources?: Source[];
  toolCalls?: ToolCallInfo[];
  executionLog?: Record<string, unknown> | null;
  responseTime?: number | null;
}

export function Message({
  message,
  sources,
  toolCalls,
  executionLog,
  responseTime,
}: MessageProps) {
  const isUser = message.role === 'user';
  const isAssistant = message.role === 'assistant';
  const [copied, setCopied] = useState(false);

  const hasMetadata =
    isAssistant &&
    ((toolCalls && toolCalls.length > 0) ||
      (sources && sources.length > 0) ||
      executionLog);

  const handleCopyLog = async () => {
    if (!executionLog) return;
    await navigator.clipboard.writeText(JSON.stringify(executionLog, null, 2));
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div
      className={cn(
        'flex gap-3 p-4 animate-in fade-in slide-in-from-bottom-2 duration-300',
        isUser && 'flex-row-reverse'
      )}
    >
      {/* Avatar */}
      <div
        className={cn(
          'flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center',
          isUser ? 'bg-blue-600 text-white' : 'bg-slate-700 text-slate-200'
        )}
      >
        {isUser ? <User size={16} /> : <Bot size={16} />}
      </div>

      {/* Content */}
      <div className={cn('max-w-[85%]', isUser ? '' : 'flex-1')}>
        <div
          className={cn(
            'rounded-2xl px-4 py-3',
            isUser
              ? 'bg-blue-600 text-white rounded-br-md'
              : 'bg-slate-800 text-slate-100 rounded-bl-md border border-slate-700'
          )}
        >
          {isAssistant ? (
            <div className="prose prose-invert prose-sm max-w-none">
              <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                components={{
                  code({ className, children, ...props }) {
                    const match = /language-(\w+)/.exec(className || '');
                    const isInline = !match;
                    return isInline ? (
                      <code
                        className="bg-slate-900 px-1.5 py-0.5 rounded text-sm font-mono text-blue-300"
                        {...props}
                      >
                        {children}
                      </code>
                    ) : (
                      <pre className="bg-slate-900 p-3 rounded-lg overflow-x-auto">
                        <code className={className} {...props}>
                          {children}
                        </code>
                      </pre>
                    );
                  },
                  a({ href, children }) {
                    return (
                      <a
                        href={href}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-blue-400 hover:text-blue-300 underline transition-colors"
                      >
                        {children}
                      </a>
                    );
                  },
                  strong({ children }) {
                    return (
                      <strong className="text-blue-200">{children}</strong>
                    );
                  },
                }}
              >
                {message.content}
              </ReactMarkdown>
            </div>
          ) : (
            <p className="text-sm leading-relaxed">{message.content}</p>
          )}
        </div>

        {/* Per-message metadata: ToolCalls + Sources + Copy Log */}
        {hasMetadata && (
          <div className="mt-1">
            <ToolCallDisplay toolCalls={toolCalls ?? []} />
            <SourcesPanel sources={sources ?? []} responseTime={responseTime} />

            {executionLog && (
              <div className="mt-3 pt-3 border-t border-slate-700/50 flex justify-end">
                <button
                  onClick={handleCopyLog}
                  className={cn(
                    'flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-[11px]',
                    'bg-slate-800/50 border border-slate-700/50',
                    'hover:bg-slate-800 hover:border-slate-600',
                    'text-slate-500 hover:text-blue-400',
                    'transition-all duration-200'
                  )}
                >
                  {copied ? (
                    <>
                      <ClipboardCheck size={11} />
                      <span className="text-blue-400">Copiado!</span>
                    </>
                  ) : (
                    <>
                      <ClipboardCopy size={11} />
                      Copiar logs
                    </>
                  )}
                </button>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
