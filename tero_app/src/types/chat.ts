

export interface ChatMessage {
  id: string | number;
  role: "user" | "assistant" | "system";
  content?: string;
  isLoading?: boolean;
}


export interface ChatSession {
  id: number | string;
  title?: string;
  read?: boolean;
  isLoading?: boolean;
  isLastPage?: boolean;
  start?: number;
  messages?: ChatMessage[];
  hidden?: boolean;
  // Keep it open to accept any extra fields coming from the API
  [key: string]: any;
}


export interface StreamResponseMeta {
  answer?: string;
  chat_session?: ChatSession;
  user_message?: ChatMessage;
  system_answer?: ChatMessage;
  ai_free_daily_tokens_available?: number;
  ai_tokens_available?: number;
  limit?: boolean;
  done?: boolean;
  error?: string;
}

export interface FetchSessionsResponse {
  is_last_page: boolean;
  chat_sessions: ChatSession[];
}

export interface FetchMessagesResponse {
  is_last_page: boolean;
  chat_messages: ChatMessage[];
  session: ChatSession;
  start?: number;
}