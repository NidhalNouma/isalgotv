import { useState, useRef } from "react";

import { useChat } from "../../contexts/ChatsContext";

import { MessageSquare, X, PencilLine } from "lucide-react";

function HrefButton({ chat, onClose }) {
  const { currentChat, deleteChat, selectChat, updateChat } = useChat();

  const [isEditing, setIsEditing] = useState(false);
  const [editText, setEditText] = useState(chat.title || "");

  const clickTimeout = useRef(null);
  const lastTapRef = useRef(0);

  const isTouchOnlyDevice = () =>
    typeof window !== "undefined" &&
    window.matchMedia("(hover: none) and (pointer: coarse)").matches;

  const handleSingleClick = (e) => {
    e.stopPropagation();
    // Delay single-click action to detect double-click
    clearTimeout(clickTimeout.current);
    clickTimeout.current = setTimeout(() => {
      selectChat(chat.id);
      if (isTouchOnlyDevice()) {
        onClose();
      }
    }, 200);
  };

  const handleDoubleClick = (e) => {
    e.stopPropagation();
    // Cancel the pending single-click action
    clearTimeout(clickTimeout.current);
    setIsEditing(true);
  };

  const handleTouchEnd = (e) => {
    e.stopPropagation();
    const now = Date.now();
    const delta = now - lastTapRef.current;
    if (delta > 0 && delta < 300) {
      // double-tap detected
      clearTimeout(clickTimeout.current);
      setIsEditing(true);
    }
    lastTapRef.current = now;
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
        className={`group flex items-center gap-3 px-3 py-3 rounded-md cursor-pointer hover:bg-text/20 transition-colors ${
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
          className="input-text flex-1"
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
    <div
      role="button"
      tabIndex={0}
      onClick={handleSingleClick}
      onTouchEnd={handleTouchEnd}
      key={chat.id}
      className={`group flex items-center gap-2 px-3 py-3 rounded-md cursor-pointer hover:bg-text/20 transition-colors ${
        chat.id === currentChat ? "bg-text/10" : ""
      }`}
    >
      <h4 className="flex items-center gap-3 text-text/80 flex-1 min-w-0">
        <MessageSquare className="w-4 h-4 flex-shrink-0" />
        <span className="truncate text-sm">{editText}</span>
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
          deleteChat(chat.id);
        }}
        className="text-text/40 hover:text-loss opacity-0 group-hover:opacity-100 transition-opacity"
      >
        <X className="w-4 aspect-square" />
      </button>
    </div>
  );
}

export default HrefButton;
