import { useState } from "react";

const csrf_token = document.getElementById("isalgo-ai").getAttribute("csrf-token");

export function useChatHook() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [limit, setLimit] = useState(false);

  const sendMessage = async (userMessage, messages) => {
    console.log(userMessage)
    if (!userMessage) return;
    if (!userMessage?.trim()) return;

    setLoading(true);
    setError(null);
    setLimit(false);

    try {
      const response = await fetch("/p/ai/chat/", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": csrf_token,  // Include CSRF token here
        },
        credentials: "include",  // Ensure cookies are sent
        body: JSON.stringify({ 
          userMessage, 
          messages,
          csrfmiddlewaretoken: csrf_token  // Include CSRF token in the body
        }),
      });

      console.log(response)

      if (!response.ok) {
        throw new Error("Failed to get response");
      }

      const data = await response.json();

      if(data.todat_limit_hit) {
        setLimit(true);
        return null;
      }
      return data.response;
    } catch (err) {
      console.error("Error fetching response:", err);
      setError("Failed to get response");
    } finally {
      setLoading(false);
    }
  };

  return { sendMessage, loading, error, limit };
}