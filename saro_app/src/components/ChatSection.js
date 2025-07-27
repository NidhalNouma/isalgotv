import { Fragment } from "react";

import EmptyState from "./EmptyChatState";
import ChatState from "./ChatState";

import { useUser } from "../contexts/UserContext";
import { useChatHook } from "../hooks/useChatHook";

function ChatSection() {
  const { user } = useUser();

  const {
    chat,
    messages,

    handleSendMessage,
    handleTypingComplete,
  } = useChatHook();

  return (
    <Fragment>
      {messages.length === 0 ? (
        <EmptyState onSendMessage={handleSendMessage} />
      ) : (
        <ChatState
          user={user}
          messages={messages}
          // disable={chat.isLoading}
          error={chat.error}
          limit={chat.limit}
          onSendMessage={handleSendMessage}
          onTypingComplete={handleTypingComplete}
        />
      )}
    </Fragment>
  );
}

export default ChatSection;
