import { useEffect, useRef, useState } from "react";
import ChatMessage from "./ChatMessage";
import ChatInput from "./ChatInput";

export default function ChatState({
  messages,
  typingMessage,
  isTyping,
  onSendMessage,
  onTypingComplete,
}) {
  const messagesRef = useRef(null);

  useEffect(() => {
    const element = messagesRef.current;
    if (element) {
      element.scrollTop = element.scrollHeight;
    }
  }, [messages, typingMessage]);

  return (
    <div className="flex flex-col h-full">
      <div
        ref={messagesRef}
        className="flex-1 overflow-y-auto scrollbar-hide scroll-smooth"
      >
        {messages.map((message) => (
          <ChatMessage key={message.id} message={message} />
        ))}
        {typingMessage && (
          <ChatMessage
            message={typingMessage}
            isTyping={true}
            onComplete={onTypingComplete}
          />
        )}
      </div>
      <div className="">
        <ChatInput onSend={onSendMessage} disabled={isTyping} />
      </div>
    </div>
  );
}
