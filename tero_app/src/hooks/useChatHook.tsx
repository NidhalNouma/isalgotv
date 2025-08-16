import { useState, useEffect } from "react";
import { useChat } from "../contexts/ChatsContext";
import { useUser } from "../contexts/UserContext";
import { getStreamAnswer } from "../api/chat";

import { AI_MODELS, type AIModel } from "../constant";

// --------- Types ---------
export interface ChatMessage {
  id: string | number;
  role: "user" | "assistant" | "system";
  content?: string;
  isLoading?: boolean;
}

export interface ChatSession {
  id: string | number;
  name?: string;
  messages: ChatMessage[];
  error?: string | null;
  limit?: boolean;
  isLoading?: boolean;
  hidden?: boolean;
}

interface StreamResponseMeta {
  answer?: string;
  chat_session?: ChatSession;
  user_message?: ChatMessage;
  system_answer?: ChatMessage;
  ai_free_daily_tokens_available?: number;
  ai_tokens_available?: number;
  limit?: boolean;
  done?: boolean;
  error?: string;
}

// Hook that manages a single chat session state and sending/streaming
export function useChatHook() {
  const { user, updateTokens } = useUser();
  const {
    chats,
    setChats,
    newChatAdded,
    newMessagesAdded,
    currentChat,
    selectChat,
  } = useChat();

  const chat: ChatSession | null =
    (chats as ChatSession[]).find(
      (c) => String(c.id) === String(currentChat)
    ) || null;

  let messages: ChatMessage[] = chat ? chat.messages || [] : [];

  // console.log("=== ", chat);

  function setChatMessages(
    chatId: string | number | null | undefined,
    msgs: ChatMessage[],
    error: string | null = null,
    limit = false,
    isLoading = false
  ): void {
    const id = String(chatId) ?? "new-chat";
    setChats((prev) => {
      return prev.map((c) => {
        if (String(c.id) === id) {
          return {
            ...c,
            messages: msgs || c.messages,
            error,
            limit,
            isLoading,
          } as ChatSession;
        }
        return c as ChatSession;
      });
    });
  }

  function setTypingMessage(
    chatId: string | number | null | undefined,
    messageId: string | number,
    reply: string
  ) {
    const id = String(chatId) ?? "new-chat";
    setChats((prev) => {
      return prev.map((c) => {
        if (String(c.id) === id) {
          return {
            ...c,
            messages: (c.messages || []).map((msg) =>
              msg.id === messageId
                ? {
                    ...msg,
                    content: reply,
                    isLoading: true,
                  }
                : msg
            ),
          } as ChatSession;
        }
        return c as ChatSession;
      });
    });
  }

  function addTempChatMessages(chatName: string, msgs: ChatMessage[]) {
    const id = "new-chat";
    setChats([
      ...(chats as ChatSession[]),
      {
        id,
        name: chatName,
        messages: msgs,
        hidden: true,
        isLoading: true,
      } as ChatSession,
    ]);
    selectChat(id);
  }

  // --- Per-chat drafts: each chat id has its own input/files ---
  const activeId = String(currentChat ?? "new-chat");

  const [drafts, setDrafts] = useState<Record<string, string>>({});
  const [fileDrafts, setFileDrafts] = useState<Record<string, File[]>>({});

  const input = drafts[activeId] ?? "";
  const files = fileDrafts[activeId] ?? [];

  const setInput = (next: string | ((prev: string) => string)) => {
    setDrafts((prev) => {
      const prevVal = prev[activeId] ?? "";
      const nextVal =
        typeof next === "function"
          ? (next as (p: string) => string)(prevVal)
          : next;
      if (nextVal === prevVal) return prev;
      return { ...prev, [activeId]: nextVal };
    });
  };

  const setFiles = (next: File[] | ((prev: File[]) => File[])) => {
    setFileDrafts((prev) => {
      const prevVal = prev[activeId] ?? [];
      const nextVal =
        typeof next === "function"
          ? (next as (p: File[]) => File[])(prevVal)
          : next;
      return { ...prev, [activeId]: nextVal };
    });
  };

  const [model, setModel] = useState<AIModel>(AI_MODELS![0]);

  useEffect(() => {
    function handleDjangoMessage(e: Event) {
      const ce = e as CustomEvent<{ message: string }>;
      // console.log("Received message:", ce.detail.message);
      handleSubmit(null, ce.detail?.message);
    }
    window.addEventListener(
      "teroMessage",
      handleDjangoMessage as EventListener
    );
    return () => {
      window.removeEventListener(
        "teroMessage",
        handleDjangoMessage as EventListener
      );
    };
  }, [user]);

  function parseChunks(input: string) {
    // Markers look like: \n<|TAG|>:
    const marker = /\n<\|([a-zA-Z]+)\|>:/g;

    type Chunk = { tag: string; payload: string };

    const indices: { tag: string; start: number; endOfMarker: number }[] = [];
    let m: RegExpExecArray | null;

    // Collect all marker positions and their tags
    while ((m = marker.exec(input)) !== null) {
      indices.push({
        tag: m[1].toLowerCase(),
        start: m.index,
        endOfMarker: m.index + m[0].length,
      });
    }

    // Build results with payloads (what comes after each tag)
    const result: Chunk[] = [];
    for (let i = 0; i < indices.length; i++) {
      const cur = indices[i];
      const next = indices[i + 1];
      const payloadStart = cur.endOfMarker;
      const payloadEnd = next ? next.start : input.length;
      // Preserve payload exactly as emitted (including spaces/newlines)
      const payload = input.slice(payloadStart, payloadEnd);

      result.push({ tag: cur.tag, payload });
    }

    return result;
  }

  const sendMessage = async (
    msg: string,
    files: File[] | null,
    modelName: string
  ) => {
    if (!msg?.trim()) return;

    const currentChatId = currentChat || "new-chat";
    setChatMessages(currentChatId, messages, null, false, true);

    try {
      const msgs = messages.filter((m) => m.content);

      let full_reply = "";
      const stream = (await getStreamAnswer(
        msg,
        msgs,
        files,
        modelName,
        currentChat
      )) as AsyncIterable<string> | any;

      for await (const chunk of stream as AsyncIterable<string>) {
        const chunks = parseChunks(chunk);

        console.log(chunks);

        for (const ch of chunks) {
          const tag = ch.tag;
          const payload = ch.payload ?? "";

          switch (tag) {
            case "data": {
              // Accumulate assistant text and update the typing message live
              full_reply += payload;
              break;
            }
            case "limit": {
              // Server indicates token/usage limit reached
              const last = messages[messages.length - 1];
              if (last && typeof last === "object" && last.isLoading) {
                messages = messages.slice(0, -1);
              }
              setChatMessages(currentChatId, messages, null, true);
              return;
            }
            case "error": {
              // Server sent an error payload
              throw new Error(payload || "Unknown error from stream");
            }
            case "done": {
              // Optionally the payload after <|done|>: may be a JSON meta blob
              let meta: StreamResponseMeta | undefined;
              try {
                meta = payload
                  ? (JSON.parse(payload) as StreamResponseMeta)
                  : undefined;
              } catch (_) {
                // If it's not JSON, just finish without meta
              }
              return meta;
            }
            default: {
              // Unknown tag — ignore and continue
              break;
            }
          }
        }

        console.log(full_reply);
        setTypingMessage(
          currentChatId!,
          messages[messages.length - 1].id,
          full_reply
        );
      }
    } catch (err) {
      console.error("Error fetching response:", err);

      const last = messages[messages.length - 1];
      if (last && typeof last === "object" && last.isLoading) {
        messages = messages.slice(0, -1);
      }
      setChatMessages(
        currentChat as string | number,
        messages,
        "Failed to get response"
      );

      return null;
    } finally {
    }
  };

  const handleSendMessage = async (
    messageContent: string,
    files: File[] = [],
    modelName: string
  ) => {
    let content = messageContent;
    if ((chat?.error || chat?.limit) && messages?.length > 0 && !content) {
      content = messages[messages.length - 1].content ?? "";
    }

    if (files?.length) {
      const fileNames = files.map((file) => file.name).join(", ");
      content += `\n\nAttached files: ${fileNames}`;
    }

    const tempMsg: ChatMessage = {
      id: messages.length.toString() + "_",
      role: "user",
      content: content,
    };
    const loadingMsg: ChatMessage = {
      id: (messages.length + 1).toString() + "_",
      role: "assistant",
      isLoading: true,
    };

    if (!currentChat) {
      messages = [...messages, tempMsg, loadingMsg];
      addTempChatMessages("new-chat", messages);
    } else {
      if (!chat?.error && !chat?.limit) {
        messages = [...messages, tempMsg, loadingMsg];
        setChatMessages(currentChat as string | number, messages);
      }
      if (chat?.error || chat?.limit) {
        messages = [...messages, loadingMsg];
        setChatMessages(currentChat as string | number, messages);
      }
    }

    const isNewChat = currentChat === "new-chat" || !currentChat;

    const response = (await sendMessage(
      content,
      files,
      modelName
    )) as StreamResponseMeta;

    const newMessage = response ? response.answer : null;

    const responseChat = response?.chat_session as ChatSession;
    const responseUserMessage = response?.user_message as ChatMessage;
    const responseAiMessage = response?.system_answer as ChatMessage;
    const daylyToken = response?.ai_free_daily_tokens_available;
    const aiTokensAvailable = response?.ai_tokens_available;

    if (newMessage) {
      updateTokens(daylyToken!, aiTokensAvailable!);

      if (isNewChat) {
        newChatAdded(responseChat, responseUserMessage, responseAiMessage);
      } else
        newMessagesAdded(
          responseChat.id,
          tempMsg.id,
          responseUserMessage,
          loadingMsg.id,
          responseAiMessage
        );
    }
  };

  const handleSubmit = async (
    e?: React.FormEvent | null,
    message: string | null = null
  ) => {
    e?.preventDefault();

    const msg = input.trim() || message || "";

    // console.log("Submitting message:", msg, currentChat, loading);

    if ((msg || files.length > 0) && !chat?.isLoading) {
      setInput("");
      setFiles([]);

      try {
        await handleSendMessage(msg, files, model.name);
      } catch (error) {
        console.error("Error sending message:", error);
      } finally {
      }
    }
  };

  return {
    chat,
    messages,

    input,
    files,
    setInput,
    setFiles,
    handleSubmit,

    models: AI_MODELS,
    model,
    setModel,
  };
}
