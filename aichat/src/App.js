import { Fragment, useState } from "react";
import Chat from "./pages/Chat";
import Trade from "./pages/Trade";

import { UserProvider } from "./contexts/UserContext";
import { ChatsProvider } from "./contexts/ChatsContext";

import SideBar from "./components/SideBar";

const rootDiv = document.getElementById("saro");
const isPage = rootDiv.getAttribute("is-page") === "true" ? true : false;

function App() {
  const initialPage = window.location.pathname.includes("saro/trade")
    ? "trade"
    : "chat";
  const [page, setPage] = useState(initialPage);

  const [sideBar, setSideBar] = useState(false);

  return (
    <div className="flex h-screen max-h-screen overflow-hidden">
      <UserProvider>
        <ChatsProvider>
          {isPage && (
            <SideBar
              page={page}
              changePage={setPage}
              open={sideBar}
              setOpen={setSideBar}
            />
          )}
          {page === "chat" ? (
            <Chat
              changePage={setPage}
              sideBar={sideBar}
              setSideBar={setSideBar}
            />
          ) : page === "trade" ? (
            <Trade
              changePage={setPage}
              sideBar={sideBar}
              setSideBar={setSideBar}
            />
          ) : (
            <Fragment />
          )}
        </ChatsProvider>
      </UserProvider>
    </div>
  );
}

export default App;
