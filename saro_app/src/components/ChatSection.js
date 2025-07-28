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
    chat,
    messages,

    handleSendMessage,
    handleTypingComplete,
  } = useChatHook();

  // console.log("ChatSection rendered", chat);

  return (
    <Fragment>
      {messages.length === 0 && !currentChat ? (
        <EmptyState onSendMessage={handleSendMessage} />
      ) : (
        <ChatState
          user={user}
          messages={messages}
          disable={chat.isLoading}
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
