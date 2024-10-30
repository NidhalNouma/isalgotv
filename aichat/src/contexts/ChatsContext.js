import { createContext, useContext, useState, useEffect } from "react";

const ChatsContext = createContext();

export const ChatsProvider = ({ children }) => {
  const [chats, setChats] = useState([]);
  const [currentChat, setCurrentChat] = useState(null);

  const createNewChat = () => {
    // if (currentChat) {
    //   const c = chats.find((c) => c.id === currentChat);
    //   if (c && c.messages?.length === 0) return;
    // }
    setCurrentChat(null);
    // const newChat = {
    //   id: chats.length + "-chat",
    //   title: "New chat",
    //   messages: [],
    // };
    // setChats((prev) => [...prev, newChat]);
    // setCurrentChat(newChat.id);
  };

  const createNewChatMessage = (messageContent) => {
    if (currentChat) {
      const c = chats.find((c) => c.id === currentChat);
      if (c && c.messages?.length === 0) return;
    }

    const newMessage = {
      id: "0",
      role: "user",
      content: messageContent,
    };
    const newChat = {
      id: chats.length + "-chat",
      title: "New chat",
      messages: [newMessage],
    };

    setChats((prev) => [...prev, newChat]);
    setCurrentChat(newChat.id);
  };

  const deleteChat = (id) => {
    setChats((prev) => prev.filter((chat) => chat.id !== id));
    if (currentChat === id) {
      setCurrentChat(chats[0]?.id || null);
    }
  };

  const selectChat = (id) => {
    if (currentChat !== id) {
      setCurrentChat(id);
    }
  };

  //   useEffect(() => {
  //     if (chats.length === 0) {
  //       createNewChat();
  //     }
  //   }, [chats.length]);

  return (
    <ChatsContext.Provider
      value={{
        chats,
        setChats,
        currentChat,
        setCurrentChat,
        createNewChat,
        createNewChatMessage,
        selectChat,
        deleteChat,
      }}
    >
      {children}
    </ChatsContext.Provider>
  );
};

export const useChat = () => useContext(ChatsContext);
