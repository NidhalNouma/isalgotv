import { useState, Fragment } from "react";
import Navbar from "../components/NavBar";
import SideBar from "../components/SideBar";
import TradeSection from "../components/TradeSection";

import { ChatsProvider } from "../contexts/ChatsContext";

function Trade({ changePage }) {
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const [isHovering, setIsHovering] = useState(false);

  const toggleSidebar = () => {
    setIsSidebarOpen((prev) => !prev);
    setIsHovering(false);
  };

  return (
    <Fragment>
      <div className="px-4 relative flex flex-col w-full flex-grow overflow-y-scroll scrollbar-hide">
        <Navbar
          onMenuClick={toggleSidebar}
          onMenuHover={() => setIsHovering(true)}
          className=""
          page="trade"
          changePage={changePage}
        />
        <TradeSection />
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
          page="trade"
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

export default Trade;
