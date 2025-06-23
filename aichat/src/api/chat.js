const BASE = "/saro/chat";

function getCookie(name) {
  const cookies = document.cookie.split(";").map((c) => c.trim());
  for (let c of cookies) {
    if (c.startsWith(name + "=")) {
      return decodeURIComponent(c.substring(name.length + 1));
    }
  }
  return null;
}

const csrf_token = getCookie("csrftoken");

export async function fetchChatSessions(start = 0) {
  const res = await fetch(`${BASE}/sessions/${start}/`, {
    method: "POST",

    headers: {
      "Content-Type": "application/json",
      "X-CSRFToken": csrf_token, // Include CSRF token here
    },
    body: JSON.stringify({
      csrfmiddlewaretoken: csrf_token,
    }),
  });
  return res.json();
}

export async function fetchChatMessages(sessionId, start = 0) {
  const res = await fetch(`${BASE}/messages/${sessionId}/${start}/`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-CSRFToken": csrf_token, // Include CSRF token here
    },
    body: JSON.stringify({
      csrfmiddlewaretoken: csrf_token,
    }),
  });
  return res.json();
}

export async function createChatSession(title, message, answer) {
  const res = await fetch(`${BASE}/create/`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-CSRFToken": csrf_token, // Include CSRF token here
    },
    body: JSON.stringify({
      title,
      message,
      answer,
      csrfmiddlewaretoken: csrf_token,
    }),
  });
  return res.json();
}

export async function getAnswer(message, messages, chatId = null) {
  const res = await fetch(`${BASE}/`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-CSRFToken": csrf_token, // Include CSRF token here
    },
    body: JSON.stringify({
      userMessage: message,
      messages,
      chatId,
      csrfmiddlewaretoken: csrf_token,
    }),
  });
  return res.json();
}

export async function saveChatMessage(sessionId, message, answer) {
  const res = await fetch(`${BASE}/message/${sessionId}/`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-CSRFToken": csrf_token, // Include CSRF token here
    },
    body: JSON.stringify({ message, answer, csrfmiddlewaretoken: csrf_token }),
  });
  return res.json();
}

export async function deleteChatSession(sessionId) {
  const res = await fetch(`${BASE}/sessions/${sessionId}/delete/`, {
    method: "POST",
    body: JSON.stringify({ csrfmiddlewaretoken: csrf_token }),
    headers: { "Content-Type": "application/json" },
  });
  return res.json();
}
