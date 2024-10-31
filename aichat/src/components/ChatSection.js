import { Fragment, useState } from "react";

import EmptyState from "./EmptyState";
import ChatState from "./ChatState";

import { useChat } from "../contexts/ChatsContext";

function ChatSection() {
  const {
    chats,
    setChats,
    currentChat,
    setCurrentChat,
    createNewChat,
    deleteChat,
    createNewChatMessage,
  } = useChat();

  const [isTyping, setIsTyping] = useState(false);
  const [currentTypingMessage, setCurrentTypingMessage] = useState(null);

  const handleSendMessage = (content, files) => {
    let messageContent = content;

    if (files?.length) {
      const fileNames = files.map((file) => file.name).join(", ");
      messageContent += `\n\nAttached files: ${fileNames}`;
    }

    if (!currentChat) {
      createNewChatMessage(messageContent);
    } else {
      const newMessage = {
        id: chats.length,
        role: "user",
        content: messageContent,
      };

      setChats((prev) =>
        prev.map((chat) => {
          if (chat.id === currentChat) {
            return {
              ...chat,
              messages: [...chat.messages, newMessage],
            };
          }
          return chat;
        })
      );
    }

    simulateResponse(messageContent);
  };

  const simulateResponse = async (userMessage) => {
    setIsTyping(true);

    await new Promise((resolve) => setTimeout(resolve, 1000));

    const response = `IsalGo AI is a powerful AI tool that will be available soon.`;

    const newMessage = {
      id: chats.length,
      role: "assistant",
      content: response,
    };

    setCurrentTypingMessage(newMessage);
  };

  const handleTypingComplete = () => {
    if (currentTypingMessage) {
      setChats((prev) =>
        prev.map((chat) => {
          if (chat.id === currentChat) {
            return {
              ...chat,
              title:
                chat.messages[chat.messages.length - 1].content.slice(0, 30) +
                "...",
              messages: [...chat.messages, currentTypingMessage],
            };
          }
          return chat;
        })
      );
      setCurrentTypingMessage(null);
      setIsTyping(false);
    }
  };

  const getCurrentChat = () => chats.find((chat) => chat.id === currentChat);

  const currentChatData = getCurrentChat();

  return (
    <Fragment>
      {!currentChat ? (
        <EmptyState onSendMessage={handleSendMessage} />
      ) : (
        <ChatState
          messages={currentChatData?.messages || []}
          typingMessage={currentTypingMessage}
          isTyping={isTyping}
          onSendMessage={handleSendMessage}
          onTypingComplete={handleTypingComplete}
        />
      )}
    </Fragment>
  );
}

export default ChatSection;
