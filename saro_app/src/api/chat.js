let host = window.location.hostname;
if (host.startsWith("saro.")) {
  host = host.replace("saro.", "www.");
  const port = window.location.port ? `:${window.location.port}` : "";
  const newUrl = `${window.location.protocol}//${host}${port}`;
  host = newUrl;
}
const BASE = host + "/saro/chat";

console.log("BASE URL:", BASE);

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
  try {
    const res = await fetch(`${BASE}/sessions/${start}/`, {
      method: "POST",

      headers: {
        "Access-Control-Allow-Origin": "*", // Allow all origins
        "Content-Type": "application/json",
        "X-CSRFToken": csrf_token, // Include CSRF token here
      },
    });
    return res.json();
  } catch (error) {
    console.error("Error fetching chat sessions:", error);
    throw error; // Re-throw the error for further handling if needed
  }
}

export async function fetchChatMessages(sessionId, start = 0) {
  const res = await fetch(`${BASE}/messages/${sessionId}/${start}/`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-CSRFToken": csrf_token, // Include CSRF token here
    },
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
    }),
  });
  return res.json();
}

export async function getAnswer(message, messages, chatId = null) {
  const res = await fetch(`${BASE}/response/`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-CSRFToken": csrf_token, // Include CSRF token here
    },
    body: JSON.stringify({
      userMessage: message,
      messages,
      chatId,
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
    body: JSON.stringify({ message, answer }),
  });
  return res.json();
}

export async function updateChatSession(sessionId, title) {
  const res = await fetch(`${BASE}/sessions/${sessionId}/update/`, {
    method: "POST",
    headers: { "Content-Type": "application/json", "X-CSRFToken": csrf_token },

    body: JSON.stringify({ title }),
  });
  return res.json();
}

export async function deleteChatSession(sessionId) {
  const res = await fetch(`${BASE}/sessions/${sessionId}/delete/`, {
    method: "POST",
    headers: { "Content-Type": "application/json", "X-CSRFToken": csrf_token },
  });
  return res.json();
}
