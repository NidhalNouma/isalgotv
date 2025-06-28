import { useState } from "react";
import { useChat } from "../contexts/ChatsContext";
import { getAnswer } from "../api/chat";

export function useChatHook() {
  const {
    chats,
    setChats,
    newChatAdded,

    messages,
    setMessages,
    newMessagesAdded,

    currentChat,
    setCurrentChat,

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

  const handleSendMessage = async (messageContent, files) => {
    if ((error || limit) && messages?.length > 0 && !messageContent) {
      messageContent = messages[messages.length - 1].content;
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

      const loadingMsg = {
        id: chats.length + 2,
        role: "assistant",
        isLoading: true,
      };

      setMessages((prev) => [...prev, newMessage, loadingMsg]);

      setCurrentChat("new-chat");
      await simulateResponse(messageContent, true);
    } else {
      const newMessage = {
        id: chats.length + 1,
        role: "user",
        content: messageContent,
      };
      const loadingMsg = {
        id: chats.length + 2,
        role: "assistant",
        isLoading: true,
      };

      if (!error && !limit)
        setMessages((prev) => [...prev, newMessage, loadingMsg]);
      await simulateResponse(messageContent);
    }
  };

  const simulateResponse = async (userMessage, isNewChat = false) => {
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

      if (isNewChat) {
        newChatAdded(responseChat, responseUserMessage, responseAiMessage);
      } else
        newMessagesAdded(currentChat, responseUserMessage, responseAiMessage);
    }
    setIsTyping(false);
  };

  const handleTypingComplete = async (chatId, msgId) => {
    if (currentChat === chatId) {
      setMessages((msgs) =>
        msgs.map((msg) => (msg.id === msgId ? { ...msg, isNew: false } : msg))
      );
    }
    setChats((prev) =>
      prev.map((chat) =>
        chat.id === chatId
          ? {
              ...chat,
              messages: chat.messages.map((msg) =>
                msg.id === msgId ? { ...msg, isNew: false } : msg
              ),
            }
          : chat
      )
    );
    return;
    // if (currentTypingMessage) {
    //   const newAnswer = {
    //     id: displayChats.length,
    //     role: "assistant",
    //     content: currentTypingMessage,
    //   };

    //   setDisplayChats((prev) =>
    //     prev.map((chat) => {
    //       if (chat.id === currentChat) {
    //         return {
    //           ...chat,
    //         };
    //       }
    //       return chat;
    //     })
    //   );

    //   setDisplayedMessages((prev) => [...prev, newAnswer]);

    //   setCurrentTypingMessage(null);
    //   setIsTyping(false);
    // }
  };

  return {
    currentTypingMessage,
    handleSendMessage,
    handleTypingComplete,
    // loading,
    error,
    limit,
  };
}
