import { useState, useCallback, useRef } from 'react';
import type { Message, ChatResponse, Source, ToolCallInfo } from '@/types';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

interface TokenUsage {
  prompt_tokens: number;
  completion_tokens: number;
  total_tokens: number;
  estimated_cost_usd: number;
}

interface ChatState {
  messages: Message[];
  isLoading: boolean;
  error: string | null;
  lastSources: Source[];
  lastToolCalls: ToolCallInfo[];
  responseTime: number | null;
  sessionUsage: TokenUsage;
}

const EMPTY_USAGE: TokenUsage = {
  prompt_tokens: 0,
  completion_tokens: 0,
  total_tokens: 0,
  estimated_cost_usd: 0,
};

export function useChat() {
  const [state, setState] = useState<ChatState>({
    messages: [],
    isLoading: false,
    error: null,
    lastSources: [],
    lastToolCalls: [],
    responseTime: null,
    sessionUsage: EMPTY_USAGE,
  });

  const abortControllerRef = useRef<AbortController | null>(null);

  const sendMessage = useCallback(async (content: string) => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }

    const userMessage: Message = { role: 'user', content };
    const updatedMessages = [...state.messages, userMessage];

    setState(prev => ({
      ...prev,
      messages: updatedMessages,
      isLoading: true,
      error: null,
      lastSources: [],
      lastToolCalls: [],
      responseTime: null,
    }));

    abortControllerRef.current = new AbortController();

    try {
      const response = await fetch(`${API_URL}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ messages: updatedMessages, stream: false }),
        signal: abortControllerRef.current.signal,
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `Erro HTTP: ${response.status}`);
      }

      const data: ChatResponse = await response.json();

      setState(prev => ({
        ...prev,
        messages: [...updatedMessages, data.message],
        isLoading: false,
        lastSources: data.sources,
        lastToolCalls: data.tool_calls,
        responseTime: data.response_time_ms,
        sessionUsage: data.usage
          ? {
              prompt_tokens: prev.sessionUsage.prompt_tokens + data.usage.prompt_tokens,
              completion_tokens: prev.sessionUsage.completion_tokens + data.usage.completion_tokens,
              total_tokens: prev.sessionUsage.total_tokens + data.usage.total_tokens,
              estimated_cost_usd: prev.sessionUsage.estimated_cost_usd + data.usage.estimated_cost_usd,
            }
          : prev.sessionUsage,
      }));

      return data;
    } catch (err) {
      if (err instanceof Error && err.name === 'AbortError') return null;

      const errorMessage = err instanceof Error ? err.message : 'Erro desconhecido';
      setState(prev => ({ ...prev, isLoading: false, error: errorMessage }));
      throw err;
    }
  }, [state.messages]);

  const clearChat = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    setState({
      messages: [],
      isLoading: false,
      error: null,
      lastSources: [],
      lastToolCalls: [],
      responseTime: null,
      sessionUsage: EMPTY_USAGE,
    });
  }, []);

  return {
    messages: state.messages,
    isLoading: state.isLoading,
    error: state.error,
    lastSources: state.lastSources,
    lastToolCalls: state.lastToolCalls,
    responseTime: state.responseTime,
    sessionUsage: state.sessionUsage,
    sendMessage,
    clearChat,
  };
}