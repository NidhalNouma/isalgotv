import { useState } from "react";
import { X, Search, MessageSquarePlus } from "lucide-react";

import { useChat } from "../contexts/ChatsContext";

import HrefButton from "./hrefButton";

function SideBar({ onClose }) {
  const { chats, createNewChat, isTyping } = useChat();

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

      <button
        disabled={isTyping}
        onClick={createNewChat}
        className="btn-icon ml-2  px-3 py-3 gap-3 rounded-md transition-colors"
        aria-label="new Chat"
      >
        <MessageSquarePlus className="w-3.5 aspect-auto " />
        New chat
      </button>
      <div className="flex-1 overflow-y-auto px-2">
        {filteredChats?.map((chat) => (
          <HrefButton chat={chat} onClose={onClose} />
        ))}
      </div>
    </div>
  );
}

export default SideBar;
