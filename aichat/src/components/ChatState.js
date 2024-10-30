import React from "react";
import ChatMessage from "./ChatMessage";
import ChatInput from "./ChatInput";

export default function ChatState({
  messages,
  typingMessage,
  isTyping,
  onSendMessage,
  onTypingComplete,
}) {
  return (
    <div className="flex flex-col h-full">
      <div className="flex-1 overflow-y-auto">
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
