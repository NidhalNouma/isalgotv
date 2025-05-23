import { Fragment, useState } from "react";

import EmptyState from "./EmptyState";
import ChatState from "./ChatState";

import { useUser } from "../contexts/UserContext";
import { useChat } from "../contexts/ChatsContext";
import { useChatHook } from "../hooks/useChat";

function ChatSection() {
  const { user } = useUser();
  const {
    chats,
    messages,

    currentChat,
    setCurrentChat,

    displayChats,
    setDisplayChats,
    dislayedMessages,
    setDisplayedMessages,

    createFBChat,
    sendFBMessage,
    getChatsByUser,

    isTyping,
    setIsTyping,
  } = useChat();

  const { sendMessage, loading, error, limit } = useChatHook();
  const [currentTypingMessage, setCurrentTypingMessage] = useState(null);

  const handleSendMessage = (messageContent, files) => {

    if((error || limit) && dislayedMessages?.length > 0 && !messageContent) {
      messageContent = dislayedMessages[dislayedMessages.length - 1].question;
    }

    if (files?.length) {
      const fileNames = files.map((file) => file.name).join(", ");
      messageContent += `\n\nAttached files: ${fileNames}`;
    }

    if (!currentChat) {
      const newMessage = {
        id: "0",
        role: "user",
        question: messageContent,
      };

      setDisplayedMessages((prev) => [...prev, newMessage]);

      let title  = messageContent.slice(0, 30) + "..."
      const newChat = {
        id: chats.length + "-chat",
        title,
      };

      setCurrentChat(newChat.id);
      simulateResponse(messageContent, title);
    } else {
      const newMessage = {
        id: chats.length + 1,
        role: "user",
        question: messageContent,
      };

      setDisplayedMessages((prev) => [...prev, newMessage]);
      simulateResponse(messageContent);
    }

  };

  const simulateResponse = async (userMessage, title) => {
    setIsTyping(true);

    const newMessage = await sendMessage(userMessage, messages || [])
    // await new Promise((resolve) => setTimeout(resolve, 3000));    
    // const newMessage = " await sendMessage(userMessage, messages || [])"
    if(newMessage) {
      setCurrentTypingMessage(newMessage);

      if (title) {
        let chatId = await createFBChat(user?.id, title, userMessage, newMessage)
        await getChatsByUser(user?.id)
        setCurrentChat(chatId);
      } else sendFBMessage(currentChat, userMessage, newMessage)
    } else setIsTyping(false);
  };

  const handleTypingComplete = async () => {
    if (currentTypingMessage) {
      const newAnswer = {
        id: displayChats.length,
        answer: currentTypingMessage,
      }

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

  return (
    <Fragment>
      {!currentChat ? (
        <EmptyState onSendMessage={handleSendMessage} />
      ) : (
        <ChatState
          user={user}
          messages={dislayedMessages || []}
          typingMessage={currentTypingMessage}
          isTyping={isTyping}
          loading={loading}
          error={error}
          limit={limit}
          onSendMessage={handleSendMessage}
          onTypingComplete={handleTypingComplete}
        />
      )}
    </Fragment>
  );
}

export default ChatSection;
