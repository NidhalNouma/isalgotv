
const BASE = "/chat" as const;

function getCookie(name: string): string | null {
  const cookies = document.cookie.split(";").map((c) => c.trim());
  for (const c of cookies) {
    if (c.startsWith(name + "=")) {
      return decodeURIComponent(c.substring(name.length + 1));
    }
  }
  return null;
}

const csrf_token: string | null = getCookie("csrftoken");

// Generic fetch helper with JSON response typing
async function fetchJSON<T = unknown>(url: string, init?: RequestInit): Promise<T> {
  const res = await fetch(url, init);
  if (!res.ok) {
    // Surface useful error text if possible
    let details = "";
    try {
      details = await res.text();
    } catch {}
    throw new Error(`Request failed ${res.status} ${res.statusText}${details ? `: ${details}` : ""}`);
  }
  // If the response has no content, return undefined as any
  const contentType = res.headers.get("Content-Type") || "";
  if (!contentType.includes("application/json")) {
    return (undefined as unknown) as T;
  }
  return (await res.json()) as T;
}

function jsonHeaders(): HeadersInit {
  return {
    "Content-Type": "application/json",
    "X-CSRFToken": csrf_token ?? "",
  };
}

// You can define stricter interfaces if you know your API shapes.
export type SessionId = number | string;
export type Model = string;

export interface StreamIterable extends AsyncIterable<string> {}

export async function fetchChatSessions<T = unknown>(start: number = 0): Promise<T> {
  try {
    return await fetchJSON<T>(`${BASE}/sessions/${start}/`, {
      method: "POST",
      headers: jsonHeaders(),
    });
  } catch (error) {
    console.error("Error fetching chat sessions:", error);
    throw error;
  }
}

export async function fetchChatMessages<T = unknown>(sessionId: SessionId, start: number = 0): Promise<T> {
  return fetchJSON<T>(`${BASE}/messages/${sessionId}/${start}/`, {
    method: "POST",
    headers: jsonHeaders(),
  });
}

export async function createChatSession<T = unknown>(title: string, message: string, answer: string): Promise<T> {
  return fetchJSON<T>(`${BASE}/create/`, {
    method: "POST",
    headers: jsonHeaders(),
    body: JSON.stringify({ title, message, answer }),
  });
}

export async function getAnswer<T = unknown>(
  message: string,
  messages: unknown,
  files: File[] | null,
  model: Model,
  chatId: SessionId | null = null
): Promise<T> {
  files =files
  // `files` parameter is currently unused on the server API; kept for parity.
  return fetchJSON<T>(`${BASE}/response/`, {
    method: "POST",
    headers: jsonHeaders(),
    body: JSON.stringify({ userMessage: message, messages, chatId, model }),
  });
}

export async function getStreamAnswer(
  message: string,
  messages: unknown,
  files: File[] | null,
  model: Model,
  chatId: SessionId | null = null
): Promise<StreamIterable> {
  files = files
  const res = await fetch(`${BASE}/stream_response/`, {
    method: "POST",
    headers: jsonHeaders(),
    body: JSON.stringify({ userMessage: message, messages, chatId, model }),
  });

  if (!res.body) {
    throw new Error("Streaming response has no body");
  }

  const reader = res.body.getReader();
  const decoder = new TextDecoder("utf-8");

  async function* iterator(): AsyncGenerator<string> {
    try {
      while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        yield decoder.decode(value, { stream: true });
      }
    } finally {
      try {
        reader.releaseLock();
      } catch {}
    }
  }

  return {
    [Symbol.asyncIterator]: iterator,
  } as StreamIterable;
}

export async function saveChatMessage<T = unknown>(sessionId: SessionId, message: string, answer: string): Promise<T> {
  return fetchJSON<T>(`${BASE}/message/${sessionId}/`, {
    method: "POST",
    headers: jsonHeaders(),
    body: JSON.stringify({ message, answer }),
  });
}

export async function updateChatSession<T = unknown>(sessionId: SessionId, title: string): Promise<T> {
  return fetchJSON<T>(`${BASE}/sessions/${sessionId}/update/`, {
    method: "POST",
    headers: jsonHeaders(),
    body: JSON.stringify({ title }),
  });
}

export async function markChatSessionAsRead<T = unknown>(sessionId: SessionId): Promise<T> {
  return fetchJSON<T>(`${BASE}/sessions/${sessionId}/read/`, {
    method: "POST",
    headers: jsonHeaders(),
    body: JSON.stringify({ read: true }),
  });
}

export async function deleteChatSession<T = unknown>(sessionId: SessionId): Promise<T> {
  return fetchJSON<T>(`${BASE}/sessions/${sessionId}/delete/`, {
    method: "POST",
    headers: jsonHeaders(),
  });
}
