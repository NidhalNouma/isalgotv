import { createContext, useContext, useState, useEffect } from "react";

import { useUser } from "./UserContext";

import {
  fetchChatSessions,
  fetchChatMessages,
  deleteChatSession,
  updateChatSession,
  saveChatMessage,
  createChatSession,
} from "../api/chat";

const ChatsContext = createContext();

export const ChatsProvider = ({ children }) => {
  const [currentChat, setCurrentChat] = useState(null);

  const selectChat = (id) => {
    setCurrentChat(id);
  };

  const { user } = useUser();

  const [chats, setChats] = useState([]);
  const [loadingChats, setLoadingChats] = useState(false);

  function retrieveChats() {
    setLoadingChats(true);
    fetchChatSessions(chats.length).then((data) => {
      setChats(data.chat_sessions);
      setLoadingChats(false);
    });
  }

  function newChatAdded(chat, userMessage, answer) {
    let newChat = chat;
    newChat.messages = [userMessage, answer];
    setChats((prev) => [newChat, ...prev]);

    setCurrentChat(chat.id);
  }

  async function deleteChat(chatId) {
    if (!chatId || !user) return;
    const response = await deleteChatSession(chatId);

    setChats((prev) => prev.filter((c) => c.id !== chatId));

    setCurrentChat(null);
    setDisplayedMessages([]);
  }

  async function updateChat(chatId, title) {
    if (!chatId || !user) return;
    const response = await updateChatSession(chatId, title);
    setChats((prev) =>
      prev.map((c) => {
        if (c.id === chatId) {
          return response.chat_session;
        }
        return c;
      })
    );
  }

  useEffect(() => {
    if (user) retrieveChats();
  }, [user]);

  const [messages, setMessages] = useState([]);
  const [loadingMessages, setLoadingMessages] = useState(false);

  function newMessagesAdded(chatId, userMessage, answer) {
    const chat = chats.find((c) => c.id === chatId);
    if (chat) {
      console.log("Adding new messages to chat:", chatId);
      if (currentChat === chatId) {
        setMessages([
          ...(chat.messages || []),
          userMessage,
          { ...answer, isNew: true },
        ]);
      }
      setChats((prev) =>
        prev.map((c) => {
          if (c.id === chatId) {
            return {
              ...c,
              messages: [...(chat.messages || []), userMessage, answer],
            };
          }
          return c;
        })
      );
    }
  }

  function getMessagesByChat() {
    if (!currentChat) return;
    console.log("Getting messages for chat:", currentChat);
    if (currentChat.toString().includes("new")) return;

    let chat = chats.find((c) => c.id === currentChat);
    if (chat && chat.messages && chat.messages.length > 0) {
      setMessages(chat.messages);
      return;
    }

    setLoadingMessages(true);
    fetchChatMessages(currentChat, 0).then((data) => {
      const isLastPage = data.is_last_page;
      const newMessages = data.chat_messages;
      const session = data.session;
      const start = data.start || 0;
      setMessages(newMessages);
      setChats((prev) =>
        prev.map((c) => {
          if (c.id === currentChat) {
            return { ...session, start, isLastPage, messages: newMessages };
          }
          return c;
        })
      );
      setLoadingMessages(false);
    });
  }

  function getOlderMessages() {
    if (loadingMessages) return;
    if (!currentChat) return;
    if (currentChat.toString().includes("new")) return;
    const chat = chats.find((c) => c.id === currentChat);
    if (!chat || chat.isLastPage) return;
    console.log("Getting older messages for chat:", chat);
    setLoadingMessages(true);
    fetchChatMessages(currentChat, messages.length).then((data) => {
      const isLastPage = data.is_last_page;
      const oldMessages = data.chat_messages;
      const session = data.session;
      const start = data.start || 0;
      if (chat.start === start) {
        setLoadingMessages(false);
        return;
      }
      let newMessages = [...oldMessages, ...chat.messages];
      setMessages(newMessages);
      setChats((prev) =>
        prev.map((c) => {
          if (c.id === currentChat) {
            return {
              ...session,
              isLastPage,
              start,
              messages: newMessages,
            };
          }
          return c;
        })
      );
      setLoadingMessages(false);
    });
  }

  useEffect(() => {
    if (currentChat) {
      getMessagesByChat();
    }
  }, [currentChat]);

  const [dislayedMessages, setDisplayedMessages] = useState(messages);

  useEffect(() => {
    setDisplayedMessages(messages);
  }, [messages]);

  const [displayChats, setDisplayChats] = useState(chats);
  useEffect(() => {
    setDisplayChats(chats);
  }, [chats]);

  const createNewChat = () => {
    // if (currentChat) {
    //   const c = chats.find((c) => c.id === currentChat);
    //   if (c && c.messages?.length === 0) return;
    // }
    setMessages([]);
    setCurrentChat(null);
    setDisplayedMessages([]);
    // const newChat = {
    //   id: chats.length + "-chat",
    //   title: "New chat",
    //   messages: [],
    // };
    // setChats((prev) => [...prev, newChat]);
    // setCurrentChat(newChat.id);
  };

  const [isTyping, setIsTyping] = useState(false);

  return (
    <ChatsContext.Provider
      value={{
        chats,
        newChatAdded,
        messages,
        newMessagesAdded,
        getOlderMessages,

        currentChat,
        setCurrentChat,

        createNewChat,
        selectChat,
        deleteChat,
        updateChat,

        displayChats,
        setDisplayChats,
        dislayedMessages,
        setDisplayedMessages,
        createContext,

        isTyping,
        setIsTyping,

        retrieveChats,
      }}
    >
      {children}
    </ChatsContext.Provider>
  );
};

export const useChat = () => useContext(ChatsContext);
