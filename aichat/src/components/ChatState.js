import { Fragment, useEffect, useRef } from "react";
import ChatMessage from "./ChatMessage";
import ChatInput from "./ChatInput";

export default function ChatState({
  user,
  messages,
  typingMessage,
  isTyping,
  loading,
  error,
  limit,
  onSendMessage,
  onTypingComplete,
}) {
  const messagesRef = useRef(null);

  useEffect(() => {
    const element = messagesRef.current;
    if (element) {
      element.style.scrollBehavior = "auto";
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
          <Fragment key={message.id}>
            { message.question && <ChatMessage message={message.question} isUser={true} /> }
            { message.answer && <ChatMessage message={message.answer} isUser={false} /> }
          </Fragment>
        ))}
        {loading && (
          <ChatMessage
              key="loading"
              isUser={false}
              loading={loading}
            />
         )} 
        {typingMessage && (
          <ChatMessage
            isUser={false}
            message={typingMessage}
            isTyping={isTyping}
            onComplete={onTypingComplete}
          />
        )}
      </div>
      <div className="">
        {limit && (
          <aside className="mx-auto md:px-2 px-0 max-w-3xl">
            <div className="text-text bg-text/10 px-4 py-2 rounded overflow-hidden">
              {user.hasSubscription ? 
                <p className="text-sm inline">
                  You have reached the limit of the day, You can buy some more tokens to continue using our AI tools.
                  <span className="float-right">
                    <a className="text-xs border border-text/60 py-0.5 px-2 rounded whitespace-nowrap ms-2" href="/p/membership/">Buy here</a>
                  </span>
                </p>
              :
                <p className="text-sm inline">
                  You have reached the limit of the day, subscribe to continue using the service without limits.
                  <span className="float-right">
                    <a className="text-xs border border-text/60 py-0.5 px-2 rounded whitespace-nowrap ms-2" href="/p/membership/">Subscribe here</a>
                  </span>
                </p>
              }
            </div>
          </aside>
        )}
        {error && (
          <aside className="mx-auto md:px-2 px-0 max-w-3xl">
            <div className="text-error bg-error/10 px-4 py-2 rounded overflow-hidden">
              <p className="text-sm inline">
                {error}
                <span className="float-right">
                  <button className="text-xs border border-error/60 py-0.5 px-2 rounded whitespace-nowrap ms-2" onClick={() => onSendMessage()}>Retry</button>
                </span>
              </p>
            </div>
          </aside>
        )}
        <ChatInput onSend={onSendMessage} disabled={isTyping} />
      </div>
    </div>
  );
}
