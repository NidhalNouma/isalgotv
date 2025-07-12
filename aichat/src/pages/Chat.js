import { useState, useEffect, useRef, Fragment } from "react";
import Navbar from "../components/NavBar";
import ChatSection from "../components/ChatSection";

import { useChat } from "../contexts/ChatsContext";
import { useUser } from "../contexts/UserContext";

function Chat({ changePage, sideBar, setSideBar }) {
  const { user } = useUser();
  const { retrieveChats } = useChat();

  // Track if chats have been retrieved once
  const hasFetchedChats = useRef(false);

  useEffect(() => {
    // alert(sideBar);
    if (sideBar && user && !hasFetchedChats.current) {
      retrieveChats();
      hasFetchedChats.current = true;
    }
  }, [sideBar, user]);

  return (
    <div className="px-4 relative flex flex-col w-full flex-grow max-h-full overflow-hidden scrollbar-hide">
      <Navbar
        className=""
        page="chat"
        changePage={changePage}
        setSideBar={setSideBar}
      />
      <ChatSection />
    </div>
  );
}

export default Chat;
