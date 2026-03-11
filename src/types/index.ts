/**
 * Tipos TypeScript para o Agente de Direito Laboral
 */

export interface Message {
  role: 'user' | 'assistant' | 'system' | 'tool';
  content: string;
  tool_calls?: ToolCall[];
  tool_call_id?: string;
  name?: string;
}

export interface ToolCall {
  id: string;
  type: 'function';
  function: {
    name: string;
    arguments: string;
  };
}

export interface Source {
  title: string;
  url: string;
  snippet?: string;
}

export interface ToolCallInfo {
  name: string;
  arguments: Record<string, unknown>;
  result?: string;
  error?: string;
}

export interface TokenUsage {
  prompt_tokens: number;
  completion_tokens: number;
  total_tokens: number;
  estimated_cost_usd: number;
}

export interface ChatResponse {
  message: Message;
  sources: Source[];
  tool_calls: ToolCallInfo[];
  response_time_ms: number;
  usage: TokenUsage;
  execution_log?: Record<string, unknown> | null;
}

export interface ChatRequest {
  messages: Message[];
}

export interface EvaluationCase {
  id: string;
  question: string;
  category: 'Basic' | 'Medium' | 'Advanced' | 'Limit';
  expected_topics: string[];
  requires_calculation?: boolean;
  requires_citation?: boolean;
}

export interface EvaluationResult {
  case: EvaluationCase;
  response: string;
  sources: Source[];
  tool_calls: ToolCallInfo[];
  correctness_score: number;
  citation_score: number;
  refusal_score: number;
  response_time_ms: number;
  timestamp: string;
}

export interface EvaluationSummary {
  total_cases: number;
  avg_correctness: number;
  avg_citation: number;
  avg_refusal: number;
  avg_response_time_ms: number;
  results_by_category: Record<
    string,
    {
      count: number;
      avg_correctness: number;
      avg_citation: number;
      avg_response_time_ms: number;
    }
  >;
  detailed_results: EvaluationResult[];
  timestamp: string;
}

export interface HealthResponse {
  status: string;
  version?: string;
  timestamp?: string;
}

export interface OfficialSource {
  name: string;
  url: string;
  description: string;
}
