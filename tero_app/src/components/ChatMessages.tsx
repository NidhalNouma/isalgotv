import { Fragment, useLayoutEffect, useRef } from "react";
import ChatMessage from "./ChatMessage";

import { ChatScrollContainer } from "../ui/ScrollableContainer";

import { useChat } from "../contexts/ChatsContext";
import { useUser } from "../contexts/UserContext";

// Types

interface Message {
  id: string | number;
  role: "user" | "assistant" | "system";
  content?: string;
  isNew?: boolean;
  isLoading?: boolean;
  parent_id?: number | null;
  liked?: boolean | null;
}

interface ChatMessagesProps {
  messages: Message[];
  siblingsMap?: Record<string, (string | number)[]>;
  disable?: boolean;
  error?: string | null;
  limit?: boolean;
  handleSendMessage: (
    e: React.FormEvent,
    message: string | null | undefined,
  ) => void | Promise<void>;
  startEdit?: (messageId: string | number) => void;
  editingMessageId?: string | number | null;
  switchToBranch?: (
    parentId: string | number,
    targetSiblingId: string | number,
  ) => Promise<void>;
  likeMessage?: (messageId: string | number) => Promise<void>;
  dislikeMessage?: (messageId: string | number) => Promise<void>;
  Input: React.ReactNode;
}

// Optional global declaration for buyAiToken button
declare global {
  interface Window {
    buyAiToken?: () => void;
  }
}

export default function ChatMessages({
  messages,
  siblingsMap,
  disable,
  error,
  limit,
  handleSendMessage,
  startEdit,
  editingMessageId,
  switchToBranch,
  likeMessage,
  dislikeMessage,
  Input,
}: ChatMessagesProps) {
  const { user } = useUser();

  const messagesRef = useRef<HTMLDivElement | null>(null);
  const { getOlderMessages } = useChat();

  // Keep the bottom spacer alive after streaming ends; reset when user sends next message.
  // Computed synchronously during render (no useEffect) to avoid a 1-frame flicker.
  const prevDisableRef = useRef(disable);
  const spacerActiveRef = useRef(false);
  if (prevDisableRef.current === true && disable === false) {
    spacerActiveRef.current = true;
  }
  prevDisableRef.current = disable;
  if (messages[messages.length - 1]?.isLoading) {
    spacerActiveRef.current = false;
  }
  // Track scroll height when loading older messages
  const isFetchingOlderRef = useRef<boolean>(false);
  // Scroll only once when the loading placeholder first appears (not on every streaming token)
  const prevLastIsLoadingRef = useRef<boolean>(false);

  // Capture scroll metrics BEFORE the DOM commits (render phase).
  // messagesRef still points at the old DOM here.
  const preRenderRef = useRef({ scrollHeight: 0, scrollTop: 0 });
  if (messagesRef.current) {
    preRenderRef.current = {
      scrollHeight: messagesRef.current.scrollHeight,
      scrollTop: messagesRef.current.scrollTop,
    };
  }

  // When scrolled near the bottom (since list is reversed), load older messages
  const handleScroll = () => {
    const el = messagesRef.current;
    // Don't trigger if no element or already fetching
    if (!el || isFetchingOlderRef.current) return;

    if (
      Math.abs(el.scrollHeight) - Math.abs(el.scrollTop) <=
      (el.scrollHeight * 25) / 100
    ) {
      isFetchingOlderRef.current = true;
      (getOlderMessages as () => void)();
    }
  };

  // Runs AFTER DOM commit but BEFORE paint.
  // Compensate for content height growth during streaming so the
  // viewport stays still instead of chasing the growing message.
  useLayoutEffect(() => {
    const el = messagesRef.current;
    if (!el || messages.length === 0) return;

    if (isFetchingOlderRef.current) {
      isFetchingOlderRef.current = false;
      return;
    }

    const lastMsg = messages[messages.length - 1];
    const isLastLoading = Boolean(lastMsg?.isLoading);

    // First time the loading placeholder appears → scroll to bottom
    if (isLastLoading && !prevLastIsLoadingRef.current) {
      el.scrollTop = 0; // 0 = visual bottom in flex-col-reverse
      prevLastIsLoadingRef.current = isLastLoading;
      return;
    }
    prevLastIsLoadingRef.current = isLastLoading;

    // During streaming: freeze the viewport by offsetting scrollTop
    // by however much the content grew.
    if (isLastLoading) {
      const { scrollHeight: prevH, scrollTop: prevT } = preRenderRef.current;
      const delta = el.scrollHeight - prevH;
      if (delta > 0) {
        el.scrollTop = prevT - delta;
      }
      return;
    }

    // For branch switches and other non-streaming list reshapes, preserve the
    // user's current viewport instead of jumping to the latest visible message.
    const { scrollHeight: prevH, scrollTop: prevT } = preRenderRef.current;
    const delta = el.scrollHeight - prevH;
    if (delta !== 0) {
      el.scrollTop = prevT - delta;
    }
  }, [messages]);

  return (
    <Fragment>
      <ChatScrollContainer onScroll={handleScroll} scrollRef={messagesRef}>
        <div className="">
          {limit && (
            <aside className="mx-auto md:px-2 px-0 max-w-3xl">
              <div className="text-text bg-text/10 px-4 py-2 rounded overflow-hidden">
                {user?.hasSubscription ? (
                  <p className="text-sm inline">
                    You’ve reached your daily usage limit. To continue using our
                    AI services, you can purchase additional AI tokens.
                    <span className="">
                      <button
                        className="text-xs border border-text/60 py-0.5 px-2 rounded whitespace-nowrap ms-2"
                        onClick={() => window.buyAiToken?.()}
                      >
                        Get Tokens
                      </button>
                      <button
                        className="text-xs border border-text/60 py-0.5 px-2 rounded whitespace-nowrap ms-2"
                        onClick={(e) =>
                          handleSendMessage(
                            e,
                            messages[messages.length - 1].content,
                          )
                        }
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
                        onClick={() => window.buyAiToken?.()}
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
                        onClick={(e) =>
                          handleSendMessage(
                            e,
                            messages[messages.length - 1].content,
                          )
                        }
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
                      onClick={(e) =>
                        handleSendMessage(
                          e,
                          messages[messages.length - 1].content,
                        )
                      }
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
          .map((message, i) => {
            // Compute sibling info for branch navigation
            const parentId =
              message.parent_id != null ? String(message.parent_id) : null;
            const siblings =
              parentId && siblingsMap ? siblingsMap[parentId] : undefined;
            const siblingCount = siblings?.length ?? 0;
            const siblingIndex = siblings
              ? siblings.findIndex((s) => String(s) === String(message.id))
              : -1;

            return (
              <ChatMessage
                key={String(message.id)}
                messageId={message.id}
                message={message.content ?? ""}
                isUser={message.role === "user"}
                loading={message.isLoading}
                liked={message.liked}
                siblingCount={siblingCount}
                siblingIndex={siblingIndex}
                siblings={siblings}
                parentId={parentId}
                onStartEdit={startEdit}
                isEditingMessage={
                  editingMessageId != null &&
                  String(editingMessageId) === String(message.id)
                }
                onLike={likeMessage}
                onDislike={dislikeMessage}
                onRetry={
                  i > 0 && messages[i - 1]?.role === "user"
                    ? async () =>
                        handleSendMessage(
                          {} as React.FormEvent,
                          messages[i - 1]?.content,
                        )
                    : undefined
                }
                onSwitchBranch={switchToBranch}
                isLoading={disable}
                style={
                  i === messages.length - 1 &&
                  (message.isLoading || spacerActiveRef.current)
                    ? {
                        minHeight: messagesRef.current
                          ? messagesRef.current.clientHeight - 90
                          : "fit-content",
                      }
                    : {}
                }
              />
            );
          })
          .reverse()}

        {/* Spacer for top margin */}
        <div className="max-w-3xl py-6" />
      </ChatScrollContainer>
      {Input}
    </Fragment>
  );
}
