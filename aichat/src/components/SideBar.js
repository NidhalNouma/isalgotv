import { Fragment, useEffect, useState } from "react";
import {
  X,
  Search,
  MessageSquarePlus,
  MessagesSquare,
  Activity,
} from "lucide-react";

import { ScrollDiv } from "./ui/ScrollableContainer";

import { useChat } from "../contexts/ChatsContext";
import { useUser } from "../contexts/UserContext";

import HrefButton from "./ui/hrefButton";

function SideBar({ onClose, page, changePage }) {
  const { user } = useUser();
  const { chats, createNewChat, isTyping, retrieveChats } = useChat();

  const [searchQuery, setSearchQuery] = useState("");

  const [filteredChats, setFilteredChats] = useState([]);

  useEffect(() => {
    if (searchQuery.length > 0) {
      let fChats = chats.filter((chat) =>
        chat.title?.toLowerCase().includes(searchQuery.toLowerCase())
      );
      setFilteredChats(fChats);
    } else setFilteredChats([...chats]);
  }, [chats, searchQuery]);

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

      {user?.isLifetime && (
        <div className="ml-3 pr-6 flex flex-col w-full justify-start items-start gap-3 ">
          <button
            className={`px-2 py-1 gap-1 btn-icon rounded-md transition-colors ml-0 w-full max-w-xs ${
              page === "chat" &&
              "text-background hover:text-background bg-title"
            } `}
            aria-label="Close Session"
            onClick={() => changePage("chat")}
          >
            <MessagesSquare className="w-3.5 aspect-auto " />
            Chat
          </button>
          <button
            className={`px-2 py-1 gap-1 btn-icon rounded-md transition-colors ml-0 w-full max-w-xs ${
              page === "trade" &&
              "text-background hover:text-background bg-title"
            } `}
            aria-label="Close Session"
            onClick={() => changePage("trade")}
          >
            <Activity className="w-3.5 aspect-auto " />
            Trade
          </button>
        </div>
      )}

      {page === "chat" && (
        <Fragment>
          <button
            // disabled={isTyping}
            onClick={() => {
              createNewChat();
              onClose();
            }}
            className="btn-icon ml-2  px-3 py-3 gap-3 rounded-md transition-colors"
            aria-label="new Chat"
          >
            <MessageSquarePlus className="w-3.5 aspect-auto " />
            New chat
          </button>
          <ScrollDiv className="px-2" onBottomReach={retrieveChats}>
            {filteredChats.length > 0 && (
              <h6 className="text-text/80 text-sm px-2 pt-3 pb-2">Chats</h6>
            )}
            {chats &&
              filteredChats.map((chat) => (
                <HrefButton key={chat.id} chat={chat} onClose={onClose} />
              ))}
          </ScrollDiv>
        </Fragment>
      )}
    </div>
  );
}

export default SideBar;
