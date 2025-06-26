import { Fragment } from "react";
import { useUser } from "../contexts/UserContext";
import { useChat } from "../contexts/ChatsContext";

import { PanelLeft, X, LogOut } from "lucide-react";

function Navbar({ className, onMenuClick, onMenuHover }) {
  const { user } = useUser();

  const { isTyping } = useChat();

  let isSidebarOpen = false;
  return (
    <Fragment>
      <nav
        className={
          " flex nav-bg items-center justify-between absolute left-0 right-0 rounded-t-xl top-0 z-40 py-3 px-3" +
          className
        }
      >
        <div className="flex items-center gap-2">
          {user && (
            <Fragment>
              <button
                // disabled={isTyping}
                onClick={onMenuClick}
                onMouseEnter={onMenuHover}
                className="p-2 btn-icon rounded-md transition-colors"
                aria-label="Toggle Sidebar"
              >
                {isSidebarOpen ? (
                  <X className="w-5 h-5 " />
                ) : (
                  <PanelLeft className="w-5 h-5" />
                )}
              </button>
            </Fragment>
          )}
        </div>
        <button
          onClick={() => {
            try {
              window.closeAiChat();
            } catch (error) {
              window.location.href = "/";
            }
          }}
          className="p-2 ml-0 btn-icon rounded-md transition-colors"
          aria-label="Close Session"
        >
          <LogOut className="w-5 h-5 " />
        </button>
      </nav>
    </Fragment>
  );
}

export default Navbar;
