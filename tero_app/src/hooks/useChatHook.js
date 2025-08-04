import { useState, useEffect, useRef } from "react";
import { useChat } from "../contexts/ChatsContext";
import { useUser } from "../contexts/UserContext";
import { getAnswer } from "../api/chat";

import { AI_MODELS } from "../constant";

export function useChatHook() {
  const { user, updateTokens } = useUser();
  const {
    chats,
    setChats,
    newChatAdded,

    newMessagesAdded,

    currentChat,
    selectChat,

    markSessionAsRead,
  } = useChat();

  const chat = chats?.find((c) => c?.id === currentChat);
  let messages = chat ? chat.messages || [] : [];

  function setChatMessages(
    chatId,
    messages,
    error = null,
    limit = false,
    isLoading = false
  ) {
    if (!chatId) chatId = "new-chat";
    setChats((prev) => {
      return prev.map((chat) => {
        if (chat.id === chatId) {
          return {
            ...chat,
            messages: messages,
            error: error,
            limit: limit,
            isLoading: isLoading,
          };
        }
        return chat;
      });
    });
  }

  function addTempChatMessages(chatName, messages) {
    let id = "new-chat";
    setChats([...chats, { id, name: chatName, messages, hidden: true }]);
    selectChat(id);
  }

  const sendMessage = async (msg, files, model) => {
    if (!msg?.trim()) return;

    setChatMessages(currentChat, messages, null, false, true);

    try {
      const msgs = messages.filter((m) => m.content);
      const data = await getAnswer(msg, msgs, model, files, currentChat);

      // console.log(data);

      if (data.error) throw new Error(data.error);

      if (data.todat_limit_hit) {
        const last = messages[messages.length - 1];
        if (last && typeof last === "object" && last.isLoading) {
          messages = messages.slice(0, -1);
        }
        setChatMessages(currentChat, messages, null, true);

        return null;
      }
      return data;
    } catch (err) {
      console.error("Error fetching response:", err);

      const last = messages[messages.length - 1];
      if (last && typeof last === "object" && last.isLoading) {
        messages = messages.slice(0, -1);
      }
      setChatMessages(currentChat, messages, "Failed to get response");

      return null;
    } finally {
    }
  };

  const handleSendMessage = async (messageContent, files, model) => {
    if (
      (chat?.error || chat?.limit) &&
      messages?.length > 0 &&
      !messageContent
    ) {
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
      messages = [...messages, newMessage, loadingMsg];

      addTempChatMessages("new-chat", messages);

      await simulateResponse(messageContent, files, model, true);
    } else {
      if (!chat?.error && !chat?.limit) {
        messages = [...messages, newMessage, loadingMsg];
        setChatMessages(currentChat, messages);
      }
      if (chat?.error || chat?.limit) {
        messages = [...messages, loadingMsg];
        setChatMessages(currentChat, messages);
      }
      await simulateResponse(
        messageContent,
        files,
        model,
        currentChat === "new-chat"
      );
    }
  };

  const simulateResponse = async (
    userMessage,
    files,
    model,
    isNewChat = false
  ) => {
    const response = await sendMessage(userMessage, files, model);

    const newMessage = response ? response.answer : null;

    const responseChat = response?.chat_session;
    const responseUserMessage = response?.user_message;
    const responseAiMessage = response?.system_answer;

    const daylyToken = response?.ai_free_daily_tokens_available;
    const aiTokensAvailable = response?.ai_tokens_available;

    if (newMessage) {
      updateTokens(daylyToken, aiTokensAvailable);

      if (isNewChat) {
        newChatAdded(responseChat, responseUserMessage, {
          ...responseAiMessage,
          isNew: responseChat.id === currentChat ? true : false,
        });
      } else
        newMessagesAdded(responseChat.id, responseUserMessage, {
          ...responseAiMessage,
          isNew: responseChat.id === currentChat ? true : false,
        });
    }
  };

  const handleTypingComplete = async (chatId, msgId) => {
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

    if (currentChat === chatId) {
      markSessionAsRead(chatId, true);
    }
    return;
  };

  return {
    chat,
    messages,

    handleSendMessage,
    handleTypingComplete,
  };
}

export function SendMessageHook(onSend, toggleAuthPopup) {
  const { user } = useUser();

  const [input, setInput] = useState("");
  const [files, setFiles] = useState([]);

  const [loading, setLoading] = useState(false);

  const [model, setModel] = useState(AI_MODELS[0]);

  const fileInputRef = useRef(null);
  const textareaRef = useRef(null);

  useEffect(() => {
    function handleDjangoMessage(e) {
      console.log("Received message:", e.detail.message);
      handleSubmit(null, e.detail.message);
    }
    window.addEventListener("teroMessage", handleDjangoMessage);
    return () => {
      window.removeEventListener("teroMessage", handleDjangoMessage);
    };
  }, [user]);

  const handleSubmit = async (e, message = null) => {
    e?.preventDefault();

    let msg = input.trim() || message;

    console.log("Submitting message:", msg, user);

    if ((msg || files.length > 0) && !loading) {
      if (!user) {
        toggleAuthPopup();
        // setInput("");
        return;
      }

      setLoading(true);

      setInput("");
      setFiles([]);

      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }
      if (textareaRef.current) {
        textareaRef.current.style.height = "auto";
      }

      try {
        await onSend(msg, files, model);
      } catch (error) {
        console.error("Error sending message:", error);
      } finally {
        setLoading(false);
      }
    }
  };

  const handleFileChange = (e) => {
    if (e.target.files) {
      setFiles(Array.from(e.target.files));
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  const handleInput = (e) => {
    const textarea = e.target;
    setInput(textarea.value);
    textarea.style.height = "auto";
    textarea.style.height = `${textarea.scrollHeight}px`;
  };

  return {
    input,
    files,
    fileInputRef,
    textareaRef,
    setInput,
    setFiles,
    handleSubmit,
    handleFileChange,
    handleKeyDown,
    handleInput,

    models: AI_MODELS,
    model,
    setModel,

    loading,
  };
}
