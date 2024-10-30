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
        <Navbar
          onMenuClick={toggleSidebar}
          onMenuHover={() => setIsHovering(true)}
          className="mx-4 pb-4 pt-6"
        />
        <div className="p-4 relative flex flex-col grow w-full overflow-y-scroll scrollbar-hide">
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
