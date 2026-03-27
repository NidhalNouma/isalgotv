import { Fragment, useEffect } from "react";
import ChatInput from "../components/ChatInput";
import ChatMessages from "../components/ChatMessages";
import EmptyState from "../components/ChatEmptyState";

import { useChat } from "../contexts/ChatsContext";
import { useChatHook } from "../hooks/useChatHook";

import { useParams } from "react-router-dom";

// ---- Types ----
// Adjust these types if you have more precise ones available from your contexts/hooks.

type ChatProps = {};

function Chat({}: ChatProps) {
  const { selectChat, currentChat } = useChat();

  const { id } = useParams<{ id: string }>();

  useEffect(() => {
    if (id) selectChat(String(id));
    else selectChat(null);
  }, [id]);

  const {
    chat,
    messages,
    siblingsMap,
    handleSubmit,
    input,
    setInput,
    files,
    setFiles,
    models,
    model,
    setModel,
    selectedAccount,
    setSelectedAccount,
    startEdit,
    isEditing,
    editingMessageId,
    cancelEdit,
    switchToBranch,
    likeMessage,
    dislikeMessage,
    // loading,
  } = useChatHook();

  const Input: React.ReactNode = (
    <ChatInput
      key={chat?.id ?? id ?? "__no_chat__"}
      onSend={handleSubmit}
      input={input}
      setInput={setInput}
      files={files}
      setFiles={setFiles}
      models={models}
      model={model}
      setModel={setModel}
      selectedAccount={selectedAccount}
      setSelectedAccount={setSelectedAccount}
      loading={chat?.isLoading || false}
      isEditing={isEditing}
      onCancelEdit={cancelEdit}
    />
  );

  return (
    <Fragment>
      {messages.length === 0 && !currentChat ? (
        <EmptyState
          Input={Input}
          setInput={setInput}
          handleSendMessage={handleSubmit}
        />
      ) : (
        <ChatMessages
          messages={messages}
          siblingsMap={siblingsMap}
          disable={Boolean(chat?.isLoading)}
          error={chat?.error ?? null}
          limit={Boolean(chat?.limit)}
          handleSendMessage={handleSubmit}
          startEdit={startEdit}
          editingMessageId={editingMessageId}
          switchToBranch={switchToBranch}
          likeMessage={likeMessage}
          dislikeMessage={dislikeMessage}
          Input={Input}
        />
      )}
    </Fragment>
  );
}

export default Chat;
