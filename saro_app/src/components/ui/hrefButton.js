import { useState, useRef, Fragment } from "react";

import { useChat } from "../../contexts/ChatsContext";

import { MessageSquare, X, PencilLine } from "lucide-react";

function HrefButton({ chat, onClose, setDeleteChatFn }) {
  const { currentChat, deleteChat, selectChat, updateChat } = useChat();

  const [isEditing, setIsEditing] = useState(false);
  const [editText, setEditText] = useState(chat.title || "");

  const isTouchOnlyDevice = () =>
    typeof window !== "undefined" &&
    window.matchMedia("(hover: none) and (pointer: coarse)").matches;

  const handleSingleClick = (e) => {
    console.log("Single click on chat:", chat);
    e.stopPropagation();
    selectChat(chat.id);
    if (isTouchOnlyDevice()) {
      if (onClose) onClose();
    }
  };

  const handleKeyDown = async (e) => {
    setEditText(e.target.value);

    if (e.key === "Escape") {
      e.preventDefault();

      setIsEditing(false);
    } else if (e.key === "Enter") {
      e.preventDefault();

      setIsEditing(false);

      if (editText.trim() !== "" && editText !== chat.title)
        await updateChat(chat.id, editText);
    }
  };

  if (isEditing) {
    return (
      <div
        key={chat.id}
        className={`group flex items-center gap-3 rounded-md cursor-pointer transition-colors ${
          chat.id === currentChat ? "bg-text/10" : ""
        }`}
      >
        <input
          type="text"
          placeholder=""
          value={editText}
          onChange={(e) => setEditText(e.target.value)}
          onBlur={() => setIsEditing(false)}
          onKeyDown={handleKeyDown}
          className="input-text text-xs flex-1"
          autoFocus
        />

        {/* <button
          onClick={(e) => {
            e.stopPropagation();
            deleteChat(chat.id);
          }}
          className="text-text/40 hover:text-loss opacity-0 group-hover:opacity-100 transition-opacity"
        >
          <X className="w-4 h-4" />
        </button> */}
      </div>
    );
  }

  return (
    <Fragment>
      <div
        role="button"
        tabIndex={0}
        onClick={handleSingleClick}
        onTouchEnd={handleSingleClick}
        key={chat.id}
        className={`group flex items-center gap-2 px-1 py-1 rounded-md cursor-pointer hover:bg-text/20 transition-colors ${
          chat.id === currentChat ? "bg-text/20" : ""
        }`}
      >
        <h4 className="flex items-center gap-1.5 text-text/80 flex-1 min-w-0">
          <MessageSquare className="w-3.5 aspect-auto flex-shrink-0" />
          <span
            className={`truncate text-sm ${
              !chat.read ? "font-bold" : "font-normal"
            }`}
          >
            {editText}
          </span>
        </h4>
        <button
          onClick={(e) => {
            e.stopPropagation();
            setIsEditing(true);
          }}
          className="text-text/40 hover:text-text opacity-0 group-hover:opacity-100 transition-opacity"
        >
          <PencilLine className="w-3.5 aspect-square" />
        </button>
        <button
          onClick={(e) => {
            e.stopPropagation();
            const deleteFn = async () => {
              await deleteChat(chat.id);
            };
            setDeleteChatFn({
              chatId: chat.id,
              deleteFn: deleteFn,
              chatTitle: chat.title,
            });
          }}
          className="text-text/40 hover:text-loss opacity-0 group-hover:opacity-100 transition-opacity"
        >
          <X className="w-4 aspect-square" />
        </button>
      </div>
    </Fragment>
  );
}

export default HrefButton;
