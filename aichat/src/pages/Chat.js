import { useState, useEffect, useRef, Fragment } from "react";
import Navbar from "../components/NavBar";
import SideBar from "../components/SideBar";
import ChatSection from "../components/ChatSection";

import { useChat } from "../contexts/ChatsContext";
import { useUser } from "../contexts/UserContext";

const rootDiv = document.getElementById("saro");
const isPage = rootDiv.getAttribute("is-page") === "true" ? true : false;

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
    <div className="flex h-screen max-h-screen">
      {isPage && (
        <SideBar
          page="chat"
          changePage={changePage}
          open={sideBar}
          setOpen={setSideBar}
        />
      )}
      <div className="px-4 relative flex flex-col w-full flex-grow overflow-y-scroll scrollbar-hide">
        <Navbar className="" page="chat" changePage={changePage} />
        <ChatSection />
      </div>
    </div>
  );
}

export default Chat;
