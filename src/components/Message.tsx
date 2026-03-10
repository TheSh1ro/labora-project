import type { Message as MessageType } from '@/types';
import { Bot, User } from 'lucide-react';
import { cn } from '@/lib/utils';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

interface MessageProps {
  message: MessageType;
}

export function Message({ message }: MessageProps) {
  const isUser = message.role === 'user';
  const isAssistant = message.role === 'assistant';

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
          isUser
            ? 'bg-blue-600 text-white'
            : 'bg-slate-700 text-slate-200'
        )}
      >
        {isUser ? <User size={16} /> : <Bot size={16} />}
      </div>

      {/* Content */}
      <div
        className={cn(
          'max-w-[85%] rounded-2xl px-4 py-3',
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
                  return <strong className="text-blue-200">{children}</strong>;
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
    </div>
  );
}