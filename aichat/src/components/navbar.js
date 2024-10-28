import { Fragment } from "react";
import { useUser } from "../contexts/UserContext";

import { PanelLeft, X, MessageSquarePlus, LogOut } from "lucide-react";

function Navbar({ className, onMenuClick, onMenuHover }) {
  const { user } = useUser();
  let isSidebarOpen = false;
  return (
    <Fragment>
      <nav
        className={
          "h-12 border-b border-text/10  flex items-center justify-between px-0 sticky top-0 z-40 " +
          className
        }
      >
        <div className="flex items-center gap-2">
          {user && (
            <Fragment>
              <button
                onClick={onMenuClick}
                onMouseEnter={onMenuHover}
                className="p-2 hover:bg-text/10 rounded-md transition-colors"
                aria-label="Toggle Sidebar"
              >
                {isSidebarOpen ? (
                  <X className="w-5 h-5 text-text/60" />
                ) : (
                  <PanelLeft className="w-5 h-5 text-text/60" />
                )}
              </button>
              <button
                //   onClick={createNewChat}
                className="p-2 hover:bg-text/10 rounded-md transition-colors"
                aria-label="New Chat"
              >
                <MessageSquarePlus className="w-5 h-5 text-text/60" />
              </button>
            </Fragment>
          )}
        </div>
        <button
          onClick={() => window.closeAiChat()}
          className="p-2 hover:bg-text/10 rounded-md transition-colors"
          aria-label="Close Session"
        >
          <LogOut className="w-5 h-5 text-text/40" />
        </button>
      </nav>
    </Fragment>
  );
}

export default Navbar;
