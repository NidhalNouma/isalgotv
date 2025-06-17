import { useState } from "react";
import Navbar from "./components/NavBar";
import SideBar from "./components/SideBar";
import ChatSection from "./components/ChatSection";

import { UserProvider } from "./contexts/UserContext";
import { ChatsProvider } from "./contexts/ChatsContext";

function App() {
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const [isHovering, setIsHovering] = useState(false);

  const toggleSidebar = () => {
    setIsSidebarOpen((prev) => !prev);
    setIsHovering(false);
  };

  return (
      <UserProvider>
        <ChatsProvider>
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
            ${isSidebarOpen || isHovering ? "translate-x-0" : "-translate-x-full"}
          `}
            onMouseLeave={() => {
              if (!isSidebarOpen) {
                setIsHovering(false);
              }
            }}
          >
            <SideBar
              onClose={() => {
                setIsSidebarOpen(false);
                setIsHovering(false);
              }}
            />
          </div>
        </ChatsProvider>
      </UserProvider>
  );
}

export default App;
