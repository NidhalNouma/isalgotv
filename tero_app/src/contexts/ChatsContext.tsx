import React, {
  createContext,
  useContext,
  useState,
  useEffect,
  useRef,
  type ReactNode,
} from "react";

import { useUser } from "./UserContext";

import {
  fetchChatSessions,
  fetchChatMessages,
  deleteChatSession,
  updateChatSession,
  markChatSessionAsRead,
} from "../api/chat";

// --- Types ---------------------------------------------------------------

export interface ChatMessage {
  // Message shape is not fully known; keep it flexible
  [key: string]: any;
}

export interface ChatSession {
  id: number | string;
  title?: string;
  read?: boolean;
  isLoading?: boolean;
  isLastPage?: boolean;
  start?: number;
  messages?: ChatMessage[];
  // Keep it open to accept any extra fields coming from the API
  [key: string]: any;
}

interface FetchSessionsResponse {
  is_last_page: boolean;
  chat_sessions: ChatSession[];
}

interface FetchMessagesResponse {
  is_last_page: boolean;
  chat_messages: ChatMessage[];
  session: ChatSession;
  start?: number;
}

export interface ChatsContextValue {
  chats: ChatSession[];
  setChats: React.Dispatch<React.SetStateAction<ChatSession[]>>;
  newChatAdded: (
    newChat: ChatSession,
    userMessage: ChatMessage,
    answer: ChatMessage
  ) => void;
  retrieveChats: () => void;
  newMessagesAdded: (
    chatId: number | string,
    userMsgTempId: number | string,
    userMessage: ChatMessage,
    responseMsgTempId: number | string,
    responseMessage: ChatMessage
  ) => void;
  getOlderMessages: () => void;
  currentChat: number | string | null;
  createNewChat: () => void;
  selectChat: (id: number | string | null) => void;
  deleteChat: (chatId: number | string) => Promise<void>;
  updateChat: (chatId: number | string, title: string) => Promise<void>;
  markSessionAsRead: (chatId: number | string, force?: boolean) => void;
}

const ChatsContext = createContext<ChatsContextValue | undefined>(undefined);

export const ChatsProvider: React.FC<{ children: ReactNode }> = ({
  children,
}) => {
  const { user } = useUser();

  const [chats, setChats] = useState<ChatSession[]>([]);
  const [loadingChats, setLoadingChats] = useState<boolean>(false);
  const [currentChat, setCurrentChat] = useState<number | string | null>(null);

  useEffect(() => {
    console.log("changing chat ,", currentChat);
  }, [currentChat]);

  function markSessionAsRead(chatId: number | string, force: boolean = false) {
    const chat = chats.find((c) => String(c.id) === String(chatId));

    if (chat && (!chat.read || force)) {
      markChatSessionAsRead(chatId).then(() => {
        setChats((prev) =>
          prev.map((c) =>
            String(c.id) === String(chatId) ? { ...c, read: true } : c
          )
        );
      });
    }
  }

  const selectChat = (id: number | string | null) => {
    if (String(currentChat) !== String(id)) {
      // Reset previous loading messages
      setChats((prev) =>
        prev.map((c) =>
          String(c.id) === String(id)
            ? {
                ...c,
                messages: c.messages?.map((msg) =>
                  msg.isLoading ? { ...msg, isLoading: false } : msg
                ),
              }
            : c
        )
      );
      // Select the new chat
      setCurrentChat(id);
    }
    if (id) markSessionAsRead(id);
  };

  const isLAstChat = useRef<boolean>(false);

  function retrieveChats() {
    if (isLAstChat.current) return;
    if (loadingChats) return;
    setLoadingChats(true);
    fetchChatSessions(chats.length as number).then((raw) => {
      const data = raw as FetchSessionsResponse;
      const isLastPage = data.is_last_page;
      isLAstChat.current = isLastPage;
      const dchats = data.chat_sessions;
      setChats((prev) => [...prev, ...dchats]);
      setLoadingChats(false);
    });
  }

  function newChatAdded(
    newChat: ChatSession,
    userMessage: ChatMessage,
    answer: ChatMessage
  ) {
    newChat.messages = [
      userMessage,
      { ...answer, isNew: true, isLoading: false },
    ];
    setChats((prev) => [newChat, ...prev]);

    setCurrentChat((prev) =>
      prev === null || String(prev).includes("new") ? newChat.id : prev
    );
  }

  async function deleteChat(chatId: number | string) {
    if (!chatId || !user) return;
    await deleteChatSession(chatId);

    setChats((prev) => prev.filter((c) => String(c.id) !== String(chatId)));

    if (chatId === currentChat) {
      setCurrentChat(null);
    }
  }

  async function updateChat(chatId: number | string, title: string) {
    if (!chatId || !user) return;
    const response: { chat_session: ChatSession } = await updateChatSession(
      chatId,
      title
    );
    setChats((prev) =>
      prev.map((c) =>
        String(c.id) === String(chatId) ? { ...c, ...response.chat_session } : c
      )
    );
  }

  const [loadingMessages, setLoadingMessages] = useState<boolean>(false);

  function newMessagesAdded(
    chatId: number | string,
    userMsgTempId: number | string,
    userMessage: ChatMessage,
    responseMsgTempId: number | string,
    responseMessage: ChatMessage
  ) {
    console.log("Adding new messages to chat:", chatId);
    setChats((prev) =>
      prev.map((c) =>
        c.id === chatId
          ? {
              ...c,
              isLoading: false,
              read: false,
              messages: c.messages?.map((msg) => {
                if (String(msg.id) === String(userMsgTempId))
                  return { ...msg, id: userMessage.id };
                else if (String(msg.id) === String(responseMsgTempId))
                  return {
                    ...msg,
                    id: responseMessage.id,
                    content: responseMessage.content,
                    // isLoading: false,
                  };

                return msg;
              }),
            }
          : c
      )
    );
  }

  function getMessagesByChat() {
    if (!currentChat) return;
    console.log("Getting messages for chat:", currentChat);
    if (currentChat.toString().includes("new")) return;

    const chat = chats.find((c) => String(c.id) === String(currentChat));
    if (chat && chat.messages && chat.messages.length > 0) {
      return;
    }

    console.log("fetching messages ...", chat);

    setLoadingMessages(true);
    fetchChatMessages(currentChat as number | string, 0).then((raw) => {
      const data = raw as FetchMessagesResponse;
      const isLastPage = data.is_last_page;
      const newMessages = data.chat_messages;
      const session = data.session;
      const start = data.start || 0;
      setChats((prev) =>
        prev.map((c) =>
          String(c.id) === String(currentChat)
            ? {
                ...session,
                start,
                isLastPage,
                messages: newMessages,
                read: true,
              }
            : c
        )
      );
      setLoadingMessages(false);
    });
  }

  function getOlderMessages() {
    if (loadingMessages) return;
    if (!currentChat) return;
    if (currentChat.toString().includes("new")) return;
    const chat = chats.find((c) => String(c.id) === String(currentChat));
    if (!chat || chat.isLastPage) return;
    console.log("Getting older messages for chat:", chat);
    setLoadingMessages(true);
    fetchChatMessages(
      currentChat as number | string,
      chat.messages?.length || 0
    ).then((raw) => {
      const data = raw as FetchMessagesResponse;
      const isLastPage = data.is_last_page;
      const oldMessages = data.chat_messages;
      const session = data.session;
      const start = data.start || 0;
      if (chat.start === start) {
        setLoadingMessages(false);
        return;
      }
      const newMessages = [...oldMessages, ...(chat.messages || [])];
      setChats((prev) =>
        prev.map((c) =>
          c.id === currentChat
            ? { ...session, isLastPage, start, messages: newMessages }
            : c
        )
      );
      setLoadingMessages(false);
    });
  }

  useEffect(() => {
    if (currentChat) {
      getMessagesByChat();
    }
  }, [currentChat]);

  const createNewChat = () => {
    setCurrentChat(null);
  };

  return (
    <ChatsContext.Provider
      value={{
        chats,
        setChats,
        newChatAdded,
        retrieveChats,
        newMessagesAdded,
        getOlderMessages,
        currentChat,
        createNewChat,
        selectChat,
        deleteChat,
        updateChat,
        markSessionAsRead,
      }}
    >
      {children}
    </ChatsContext.Provider>
  );
};

export const useChat = (): ChatsContextValue => {
  const ctx = useContext(ChatsContext);
  if (!ctx) {
    throw new Error("useChat must be used within a ChatsProvider");
  }
  return ctx;
};
