import { useState } from "react";
import { MessageSquare, X, Search } from "lucide-react";

import { useChat } from "../contexts/ChatsContext";

function SideBar({ onClose }) {
  const { chats, currentChat, deleteChat, selectChat } =
    useChat();

  const [searchQuery, setSearchQuery] = useState("");

  const filteredChats = chats.filter((chat) =>
    chat.title?.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="w-[260px] backdrop-blur-[320px] bg-background/80 rounded-xl h-full flex flex-col relative">
      <div className="absolute -z-10 inset-0 bg-gradient-to-tl from-transparent to-text/10 rounded-lg backdrop-blur-[320px]"></div>
      <div className=" flex items-center justify-between p-4 pr-1">
        <div className="relative grow">
          <input
            type="text"
            placeholder="Search chats..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full bg-transparent text-text placeholder-text/40 rounded-md py-1 pl-9 pr-3 !focus:outline-none  focus:ring-0"
          />

          <Search className="absolute left-2.5 top-2 w-4 h-4 text-text/60" />
        </div>
        <button
          onClick={onClose}
          className="btn-icon transition-colors ml-auto"
        >
          <X className="w-5 h-5" />
        </button>
      </div>
      <div className="flex-1 overflow-y-auto">
        {filteredChats?.map((chat) => (
          <div
            onClick={() => selectChat(chat.id)}
            key={chat.id}
            className={`group flex items-center gap-3 px-3 py-3 mx-2 rounded-md cursor-pointer hover:bg-text/20 transition-colors ${
              chat.id === currentChat ? "bg-text/10" : ""
            }`}
          >
            <h3
              className="flex items-center gap-3 text-text/80 flex-1 min-w-0"
            >
              <MessageSquare className="w-4 h-4 flex-shrink-0" />
              <span className="truncate text-sm">{chat.title}</span>
            </h3>
            <button
              onClick={(e) => {
                e.stopPropagation();
                deleteChat(chat.id);
              }}
              className="text-text/40 hover:text-loss opacity-0 group-hover:opacity-100 transition-opacity"
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
