import { createContext, useContext, useState, useEffect } from "react";

import { useUser } from "./UserContext";

import {
  fetchChatSessions,
  fetchChatMessages,
  deleteChatSession,
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

  useEffect(() => {
    if (user) retrieveChats();
  }, [user]);

  const [messages, setMessages] = useState([]);
  const [loadingMessages, setLoadingMessages] = useState(false);

  function newMessagesAdded(newChat, userMessage, answer) {
    const chat = chats.find((c) => c.id === newChat.id);
    if (chat) {
      const newMessages = [...(chat.messages || []), userMessage, answer];
      setMessages(newMessages);
      setChats((prev) =>
        prev.map((c) => {
          if (c.id === newChat.id) {
            return { ...c, messages: newMessages };
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
      const newMessages = data.chat_messages;
      setMessages(newMessages);
      setChats((prev) =>
        prev.map((c) => {
          if (c.id === currentChat) {
            return { ...c, messages: newMessages };
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

        currentChat,
        setCurrentChat,
        createNewChat,
        selectChat,
        deleteChat,
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
