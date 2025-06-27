import { useState } from "react";
import { useChat } from "../contexts/ChatsContext";
import { getAnswer } from "../api/chat";

export function useChatHook() {
  const {
    chats,
    newChatAdded,

    messages,
    newMessagesAdded,

    currentChat,
    setCurrentChat,
    displayChats,
    setDisplayChats,
    dislayedMessages,
    setDisplayedMessages,

    setIsTyping,
    retrieveChats,
  } = useChat();

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [limit, setLimit] = useState(false);

  const [currentTypingMessage, setCurrentTypingMessage] = useState("");

  const sendMessage = async (msg) => {
    if (!msg?.trim()) return;

    setLoading(true);
    setError(null);
    setLimit(false);

    try {
      const data = await getAnswer(msg, messages, currentChat);

      if (data.todat_limit_hit) {
        setLimit(true);
        return null;
      }
      return data;
    } catch (err) {
      console.error("Error fetching response:", err);
      setError("Failed to get response");
    } finally {
      setLoading(false);
    }
  };

  const handleSendMessage = (messageContent, files) => {
    if ((error || limit) && dislayedMessages?.length > 0 && !messageContent) {
      messageContent = dislayedMessages[dislayedMessages.length - 1].content;
    }

    if (files?.length) {
      const fileNames = files.map((file) => file.name).join(", ");
      messageContent += `\n\nAttached files: ${fileNames}`;
    }

    if (!currentChat) {
      const newMessage = {
        id: "0",
        role: "user",
        content: messageContent,
      };

      setDisplayedMessages((prev) => [...prev, newMessage]);

      let title = messageContent.slice(0, 30) + "...";
      const newChat = {
        id: chats.length + "-new",
        title,
      };

      setCurrentChat(newChat.id);
      simulateResponse(messageContent, title);
    } else {
      const newMessage = {
        id: chats.length + 1,
        role: "user",
        content: messageContent,
      };

      if (!error && !limit)
        setDisplayedMessages((prev) => [...prev, newMessage]);
      simulateResponse(messageContent);
    }
  };

  const simulateResponse = async (userMessage, title) => {
    setIsTyping(true);

    const response = await sendMessage(userMessage, messages || []);

    const newMessage = response ? response.answer : null;

    const responseChat = response.chat_session;
    const responseUserMessage = response.user_message;
    const responseAiMessage = response.system_answer;
    // await new Promise((resolve) => setTimeout(resolve, 3000));
    // const newMessage = " await sendMessage(userMessage, messages || [])"
    if (newMessage) {
      // setCurrentTypingMessage(newMessage);

      if (title) {
        newChatAdded(responseChat, responseUserMessage, responseAiMessage);
      } else
        newMessagesAdded(currentChat, responseUserMessage, responseAiMessage);
    }
    setIsTyping(false);
  };

  const handleTypingComplete = async () => {
    return;
    if (currentTypingMessage) {
      const newAnswer = {
        id: displayChats.length,
        role: "assistant",
        content: currentTypingMessage,
      };

      setDisplayChats((prev) =>
        prev.map((chat) => {
          if (chat.id === currentChat) {
            return {
              ...chat,
            };
          }
          return chat;
        })
      );

      setDisplayedMessages((prev) => [...prev, newAnswer]);

      setCurrentTypingMessage(null);
      setIsTyping(false);
    }
  };

  return {
    currentTypingMessage,
    handleSendMessage,
    handleTypingComplete,
    loading,
    error,
    limit,
  };
}
