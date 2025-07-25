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

  const sendMessage = async (msg, files, model) => {
    if (!msg?.trim()) return;

    setLoading(true);
    setError(null);
    setLimit(false);

    try {
      const data = await getAnswer(msg, messages, model, files, currentChat);

      console.log(data);

      if (data.error) throw new Error(data.error);

      if (data.todat_limit_hit) {
        setLimit(true);
        setMessages((prev) => {
          const last = prev[prev.length - 1];
          if (last && typeof last === "object" && last.isLoading) {
            return prev.slice(0, -1);
          }
          return prev;
        });
        return null;
      }
      return data;
    } catch (err) {
      console.error("Error fetching response:", err);
      setMessages((prev) => {
        const last = prev[prev.length - 1];
        if (last && typeof last === "object" && last.isLoading) {
          return prev.slice(0, -1);
        }
        return prev;
      });
      setError("Failed to get response");
    } finally {
      setLoading(false);
    }
  };

  const handleSendMessage = async (messageContent, files, model) => {
    if ((error || limit) && messages?.length > 0 && !messageContent) {
      messageContent = messages[messages.length - 1].content;
    }

    if (files?.length) {
      const fileNames = files.map((file) => file.name).join(", ");
      messageContent += `\n\nAttached files: ${fileNames}`;
    }

    const newMessage = {
      id: messages.length,
      role: "user",
      content: messageContent,
    };
    const loadingMsg = {
      id: messages.length + 1,
      role: "assistant",
      isLoading: true,
    };

    if (!currentChat) {
      setMessages((prev) => [...prev, newMessage, loadingMsg]);

      setCurrentChat("new-chat");
      await simulateResponse(messageContent, files, model, true);
    } else {
      if (!error && !limit)
        setMessages((prev) => [...prev, newMessage, loadingMsg]);
      if (error || limit) setMessages((prev) => [...prev, loadingMsg]);
      await simulateResponse(messageContent, files, model, false);
    }
  };

  const simulateResponse = async (
    userMessage,
    files,
    model,
    isNewChat = false
  ) => {
    setIsTyping(true);

    const response = await sendMessage(userMessage, files, model);

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
