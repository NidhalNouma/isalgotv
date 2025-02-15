import { useState } from "react";
import OpenAI from "openai";

// Store API Key in environment variables for security
const openai = new OpenAI({
  apiKey: document.getElementById("isalgo-ai").getAttribute("ai-key"),
  dangerouslyAllowBrowser: true, // Required for client-side use
});
document.getElementById("isalgo-ai").removeAttribute("ai-key");

export function useChatHook() {
//   const [messages, setMessages] = useState([]); // Includes system message


  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const sendMessage = async (userMessage, messages) => {
    if (!userMessage.trim()) return;


    setLoading(true);
    setError(null);

    const initialMessage = {
        role: "system",
        content:
          "You are an expert trading assistant. You specialize in answering trading-related questions and generating Pine Script strategies for TradingView. When responding, provide clear and precise trading advice, explain strategies, and include Pine Script code where relevant. Keep responses professional and concise.",
      };
    // Append user message to chat history
    const newMessages = [initialMessage, ...messages, { role: "user", content: userMessage }];
    // setMessages(newMessages);

    try {
      const response = await openai.chat.completions.create({
        model: "gpt-4-turbo", // Use GPT-4 for better responses
        messages: newMessages, // Send entire conversation history, including system prompt
        max_tokens: 500,
      });

      const aiResponse = response.choices[0].message.content;

      // Append AI response to chat history
      //   setMessages([...newMessages, { role: "assistant", content: aiResponse }]);
      return aiResponse;
    } catch (err) {
      console.error("Error fetching response:", err);
      setError("Failed to get response");
    } finally {
      setLoading(false);
    }
  };

  return {sendMessage, loading, error };
}