import React, { Fragment, useState } from "react";
import { Routes, Route, useLocation, useNavigate } from "react-router-dom";
import Chat from "./pages/Chat";
import Trade from "./pages/Trade";

import { UserProvider } from "./contexts/UserContext";
import { ChatsProvider } from "./contexts/ChatsContext";

import SideBar from "./components/SideBar";

const rootDiv = document.getElementById("saro");
const isPage = rootDiv.getAttribute("is-page") === "true" ? true : false;

function App() {
  const [sideBar, setSideBar] = useState(false);

  const navigate = useNavigate();
  const { pathname } = useLocation();
  const page = pathname.includes("saro/trade")
    ? "trade"
    : pathname.includes("saro/chat")
    ? "chat"
    : "";
  const changePage = (newPage) => {
    navigate(newPage === "trade" ? "/saro/trade" : "/saro/chat");
  };

  return (
    <div className="flex h-screen max-h-screen overflow-hidden">
      <UserProvider>
        <ChatsProvider>
          {isPage && (
            <SideBar
              page={page}
              changePage={changePage}
              open={sideBar}
              setOpen={setSideBar}
            />
          )}
          <Routes>
            <Route
              path="/saro/chat"
              element={
                <Chat
                  changePage={changePage}
                  sideBar={sideBar}
                  setSideBar={setSideBar}
                />
              }
            />
            <Route
              path="/saro/trade"
              element={
                <Trade
                  changePage={changePage}
                  sideBar={sideBar}
                  setSideBar={setSideBar}
                />
              }
            />
            <Route path="*" element={<Fragment />} />
          </Routes>
        </ChatsProvider>
      </UserProvider>
    </div>
  );
}

export default App;
