import React from "react";
import { MessageSquare, X } from "lucide-react";

function SideBar({
  chats,
  currentChat,
  onNewChat,
  onSelectChat,
  onDeleteChat,
  onClose,
}) {
  return (
    <div className="w-[260px] bg-background/90 backdrop-blur-[320px] rounded-xl h-full flex flex-col relative">
      <div className="absolute -z-10 inset-0 bg-gradient-to-tl from-primary/10 to-background/60 rounded-lg backdrop-blur-3xl"></div>
      <div className="flex items-center justify-between p-4 ">
        <button
          onClick={onNewChat}
          className="flex items-center gap-2 text-gray-300 hover:text-white transition-colors"
        >
          <MessageSquare className="w-5 h-5" />
          <span>New Chat</span>
        </button>
        <button
          onClick={onClose}
          className="text-gray-500 hover:text-gray-300 transition-colors"
        >
          <X className="w-5 h-5" />
        </button>
      </div>
      <div className="flex-1 overflow-y-auto">
        {chats?.map((chat) => (
          <div
            key={chat.id}
            className={`group flex items-center gap-3 px-3 py-3 mx-2 rounded-md cursor-pointer hover:bg-[#2A2B32] transition-colors ${
              chat.id === currentChat ? "bg-[#343541]" : ""
            }`}
          >
            <button
              onClick={() => onSelectChat(chat.id)}
              className="flex items-center gap-3 text-gray-300 flex-1 min-w-0"
            >
              <MessageSquare className="w-4 h-4 flex-shrink-0" />
              <span className="truncate text-sm">{chat.title}</span>
            </button>
            <button
              onClick={(e) => {
                e.stopPropagation();
                onDeleteChat(chat.id);
              }}
              className="text-gray-500 hover:text-red-400 opacity-0 group-hover:opacity-100 transition-opacity"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}

export default SideBar;
