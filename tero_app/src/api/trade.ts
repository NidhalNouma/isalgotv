import { csrf_token } from "../constant"

const BASE = "/trade" as const;


async function fetchJSON<T = unknown>(url: string, init?: RequestInit): Promise<T> {
  const res = await fetch(url, init);
  if (!res.ok) {
    let details = "";
    try {
      details = await res.text();
    } catch {}
    throw new Error(`Request failed ${res.status} ${res.statusText}${details ? `: ${details}` : ""}`);
  }
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

export async function fetchAccounts<T = unknown>(): Promise<T> {
  return fetchJSON<T>(`${BASE}/accounts/list/`, {
    method: "POST",
    headers: jsonHeaders(),
  });
}
