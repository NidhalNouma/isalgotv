import { Fragment, useEffect, useRef } from "react";
import ChatMessage from "./ChatMessage";
import ChatInput from "./ChatInput";

import { ChatScrollContainer } from "./ui/ScrollableContainer";

import { useChat } from "../contexts/ChatsContext";

export default function ChatState({
  user,
  messages,
  isTyping,
  error,
  limit,
  onSendMessage,
  onTypingComplete,
}) {
  const messagesRef = useRef(null);
  const { currentChat, getOlderMessages } = useChat();
  // Track scroll height when loading older messages
  const prevScrollHeightRef = useRef(0);
  const isFetchingOlderRef = useRef(false);
  // Track last message ID to only auto-scroll on new messages
  const prevLastMessageId = useRef(null);

  // When scrolled near the top, load older messages
  const handleScroll = () => {
    const el = messagesRef.current;
    // Don't trigger if no element or already fetching
    if (!el || isFetchingOlderRef.current) return;

    if (
      Math.abs(el.scrollHeight) - Math.abs(el.scrollTop) <=
      (el.scrollHeight * 25) / 100
    ) {
      // Remember current height before loading more
      prevScrollHeightRef.current = el.scrollHeight;
      isFetchingOlderRef.current = true;
      getOlderMessages();
    }
  };

  useEffect(() => {
    const el = messagesRef.current;
    if (!el || messages.length === 0) return;

    if (isFetchingOlderRef.current) {
      // // Restore scroll position after loading older messages
      // const newScrollHeight = el.scrollHeight;
      // el.scrollTop = newScrollHeight - prevScrollHeightRef.current;
      isFetchingOlderRef.current = false;
    } else {
      // Auto-scroll on new messages
      const currLastMessage = messages[messages.length - 1];
      const currLastId = currLastMessage.id;
      const prevLastId = prevLastMessageId.current;

      if (prevLastId === null || prevLastId !== currLastId) {
        el.scrollTop = el.scrollHeight;
      }
      prevLastMessageId.current = currLastId;
    }
  }, [messages]);

  return (
    <Fragment>
      <ChatScrollContainer
        scrollCta="Scroll to bottom"
        onScroll={handleScroll}
        scrollRef={messagesRef}
      >
        <div className="">
          {limit && (
            <aside className="mx-auto md:px-2 px-0 max-w-3xl">
              <div className="text-text bg-text/10 px-4 py-2 rounded overflow-hidden">
                {user.hasSubscription ? (
                  <p className="text-sm inline">
                    You’ve reached your daily usage limit. To continue using our
                    AI services, you can purchase additional AI tokens.
                    <span className="">
                      <button
                        className="text-xs border border-text/60 py-0.5 px-2 rounded whitespace-nowrap ms-2"
                        onClick={() => window.buyAiToken()}
                      >
                        Get Tokens
                      </button>
                      <button
                        className="text-xs border border-text/60 py-0.5 px-2 rounded whitespace-nowrap ms-2"
                        onClick={() => onSendMessage()}
                      >
                        Retry
                      </button>
                    </span>
                  </p>
                ) : (
                  <p className="text-sm inline">
                    You’ve reached your daily usage limit. To continue using our
                    AI services, you can either subscribe to increase your limit{" "}
                    <span className="font-semibold text-title">10 times</span>{" "}
                    or purchase additional AI tokens.
                    <span className="">
                      <button
                        className="text-xs border border-text/60 py-0.5 px-2 rounded whitespace-nowrap ms-2"
                        onClick={() => window.buyAiToken()}
                      >
                        Get Tokens
                      </button>
                      <a
                        className="text-xs border border-text/60 py-0.5 px-2 rounded whitespace-nowrap ms-2"
                        href="/p/membership/"
                      >
                        Subscribe here
                      </a>
                      <button
                        className="text-xs border border-text/60 py-0.5 px-2 rounded whitespace-nowrap ms-2"
                        onClick={() => onSendMessage()}
                      >
                        Retry
                      </button>
                    </span>
                  </p>
                )}
              </div>
            </aside>
          )}
          {error && (
            <aside className="mx-auto md:px-2 px-0 max-w-3xl">
              <div className="text-error bg-error/10 px-4 py-2 rounded overflow-hidden">
                <p className="text-sm inline">
                  {error}
                  <span className="float-right">
                    <button
                      className="text-xs border border-error/60 py-0.5 px-2 rounded whitespace-nowrap ms-2"
                      onClick={() => onSendMessage()}
                    >
                      Retry
                    </button>
                  </span>
                </p>
              </div>
            </aside>
          )}
        </div>

        {messages
          .map((message, i) => (
            <Fragment key={message.id}>
              <ChatMessage
                message={message.content}
                isUser={message.role === "user" ? true : false}
                isNew={message.isNew && i === messages.length - 1}
                loading={message.isLoading}
                onComplete={() => onTypingComplete(currentChat, message.id)}
              />
            </Fragment>
          ))
          .reverse()}
        {/* Spacer for top margin */}
        <div className="max-w-3xl py-6" />
      </ChatScrollContainer>
      <ChatInput onSend={onSendMessage} disabled={isTyping} />
    </Fragment>
  );
}
