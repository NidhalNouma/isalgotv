import { useState, useEffect, useRef, Fragment } from "react";
import Navbar from "../components/NavBar";
import SideBar from "../components/SideBar";
import ChatSection from "../components/ChatSection";

import { useChat } from "../contexts/ChatsContext";
import { useUser } from "../contexts/UserContext";

function Chat({ changePage }) {
  const { user } = useUser();
  const { retrieveChats } = useChat();

  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const [isHovering, setIsHovering] = useState(false);

  const toggleSidebar = () => {
    setIsSidebarOpen((prev) => !prev);
    setIsHovering(false);
  };

  // Track if chats have been retrieved once
  const hasFetchedChats = useRef(false);

  useEffect(() => {
    if ((isSidebarOpen || isHovering) && user && !hasFetchedChats.current) {
      retrieveChats();
      hasFetchedChats.current = true;
    }
  }, [isSidebarOpen, isHovering, user]);

  return (
    <Fragment>
      <div className="px-4 relative flex flex-col w-full flex-grow overflow-y-scroll scrollbar-hide">
        <Navbar
          onMenuClick={toggleSidebar}
          onMenuHover={() => setIsHovering(true)}
          className=""
        />
        <ChatSection />
      </div>

      <div
        className={`
            fixed left-0 top-0 h-full z-50 transition-transform duration-300 ease-in-out p-4 
            ${
              isSidebarOpen || isHovering
                ? "translate-x-0"
                : "-translate-x-full"
            }
          `}
        onMouseLeave={() => {
          if (!isSidebarOpen) {
            setIsHovering(false);
          }
        }}
      >
        <SideBar
          page="chat"
          changePage={changePage}
          onClose={() => {
            setIsSidebarOpen(false);
            setIsHovering(false);
          }}
        />
      </div>
    </Fragment>
  );
}

export default Chat;
