import { Fragment } from "react";

import EmptyState from "./EmptyChatState";
import ChatState from "./ChatState";

import { useUser } from "../contexts/UserContext";
import { useChat } from "../contexts/ChatsContext";
import { useChatHook } from "../hooks/useChatHook";

function ChatSection() {
  const { user } = useUser();
  const { currentChat } = useChat();

  const {
    messages,

    handleSendMessage,
    handleTypingComplete,

    error,
    limit,
  } = useChatHook();

  return (
    <Fragment>
      {!currentChat ? (
        <EmptyState onSendMessage={handleSendMessage} />
      ) : (
        <ChatState
          user={user}
          messages={messages}
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
