import { Fragment, useState } from "react";
import Navbar from "./components/NavBar";
import SideBar from "./components/SideBar";

import { UserProvider, useUser } from "./contexts/UserContext";
import HeroSection from "./components/HeroSection2";

function App() {
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const [isHovering, setIsHovering] = useState(false);

  const toggleSidebar = () => {
    setIsSidebarOpen((prev) => !prev);
    setIsHovering(false);
  };

  return (
    <UserProvider>
      <Navbar
        onMenuClick={toggleSidebar}
        onMenuHover={() => setIsHovering(true)}
        className="mx-4 pb-4 pt-6"
      />
      <div className="p-4 relative flex flex-col grow w-full overflow-y-scroll scrollbar-hide">
        <Main />
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
          // chats={chats}
          // currentChat={currentChat}
          // onNewChat={createNewChat}
          // onSelectChat={setCurrentChat}
          // onDeleteChat={handleDeleteChat}
          onClose={() => {
            setIsSidebarOpen(false);
            setIsHovering(false);
          }}
        />
      </div>
    </UserProvider>
  );
}

export default App;

function Main() {
  const { user } = useUser();

  return user ? (
    <Fragment>
      <div className="text-title max-w-5xl mx-auto my-auto text-center py-16">
        <h1 className="text-4xl sm:text-5xl font-medium mb-6 tracking-tight leading-tight ">
          <span className="bg-gradient-to-r from-accent via-primary/70 to-primary bg-clip-text text-transparent animate-gradient-x">
            IsalGo AI
          </span>{" "}
          is coming soon!
        </h1>
      </div>
    </Fragment>
  ) : (
    <Fragment>
      <HeroSection />
    </Fragment>
  );
}
