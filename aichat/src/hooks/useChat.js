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
      content: `
        You are IsAlgo AI, a friendly and knowledgeable trading assistant. Your purpose is to help traders in their journey by answering any trading-related questions, providing suggestions, and being productive and helpful in your responses.
    
        You specialize in trading strategies, market insights, and Pine Script coding for TradingView. If a user asks how to automate trades, refer them to:
        [IsAlgo Automation Docs](https://www.isalgo.com/docs/automate/).
    
        If a user asks how to write an alert for automation, refer them to:
        [IsAlgo Alerts Docs](https://www.isalgo.com/docs/alerts/).
    
        Maintain a friendly and professional tone while offering clear, precise advice and useful suggestions.
      `,
    };
    // Append user message to chat history
    
    let msgs = []

    for (const message of messages) {
      if (message.question) {
        msgs.push({ role: "user", content: message.question });
      } 
       if (message.answer) {
        msgs.push({ role: "assistant", content: message.answer });
      }
    }

    const newMessages = [initialMessage, ...msgs, { role: "user", content: userMessage }];
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