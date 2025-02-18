import { createContext, useContext, useState, useEffect } from "react";

import { useUser } from "./UserContext";
import { useFirebaseChat } from "../hooks/useFirebaseChat";


const ChatsContext = createContext();

export const ChatsProvider = ({ children }) => {
  const [currentChat, setCurrentChat] = useState(null);
  const { user } = useUser();

  const { chats, messages, getChatsByUser, getMessagesByChat, sendMessage: sendFBMessage, createChat: createFBChat, deleteChat: deleteFBChat, loading } = useFirebaseChat();

  const [dislayedMessages, setDisplayedMessages] = useState(messages);

  useEffect(() => {
    setDisplayedMessages(messages);
  }, [messages]);

  const [displayChats, setDisplayChats] = useState(chats);
  useEffect(() => {
    setDisplayChats(chats);
  }, [chats]);
  

  useEffect(() => {
    if(user)
       getChatsByUser(user.id);
  }, [user]);

  async function deleteChat(chatId) {
    if (!chatId || !user) return;
    await deleteFBChat(chatId);
    await getChatsByUser(user.id); 

    setCurrentChat(null);
    setDisplayedMessages([]);
  }


  const createNewChat = () => {
    // if (currentChat) {
    //   const c = chats.find((c) => c.id === currentChat);
    //   if (c && c.messages?.length === 0) return;
    // }
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

  const selectChat = async (id) => {
    if (currentChat !== id) {
      setCurrentChat(id);
      await getMessagesByChat(id);
    }
  };


  const [isTyping, setIsTyping] = useState(false);

  return (
    <ChatsContext.Provider
      value={{
        chats,
        messages,
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

        createFBChat,
        sendFBMessage,
        getChatsByUser,

        isTyping,
        setIsTyping,
      }}
    >
      {children}
    </ChatsContext.Provider>
  );
};

export const useChat = () => useContext(ChatsContext);
