import { useState, useEffect } from "react";
import {
  Routes,
  Route,
  useLocation,
  useNavigate,
  Navigate,
} from "react-router-dom";

import Chat from "./pages/Chat";
import Trade from "./pages/Trade";

import { ChatsProvider } from "./contexts/ChatsContext";
import { UserProvider } from "./contexts/UserContext";

import SideBar from "./components/SideBar";
import Navbar from "./components/NavBar";

type Page = "trade" | "chat" | "";

function App() {
  const [sideBar, setSideBar] = useState<boolean>(() => {
    const saved = localStorage.getItem("sideBar");
    return saved === "true";
  });

  useEffect(() => {
    localStorage.setItem("sideBar", String(sideBar));
  }, [sideBar]);

  const navigate = useNavigate();
  const { pathname } = useLocation();
  const page: Page = pathname.includes("/trade")
    ? "trade"
    : pathname.includes("/chat") || pathname.includes("/c/")
    ? "chat"
    : "";

  const changePage = (newPage: Page) => {
    navigate(newPage === "trade" ? "/trade" : "/chat");
  };

  return (
    <div className="relative flex h-full max-h-screen overflow-hidden bg-text/10 rounded-xl">
      <UserProvider>
        <ChatsProvider>
          <Navbar className="" setSideBar={() => setSideBar(true)} />
          <SideBar
            page={page}
            changePage={changePage}
            open={sideBar}
            setOpen={setSideBar}
          />

          <div className="px-4 relative flex flex-col w-full flex-grow max-h-full overflow-hidden scrollbar-hide">
            <Routes>
              <Route path="/chat" element={<Chat />} />
              <Route path="/c/:id" element={<Chat />} />
              <Route
                path="/trade"
                element={
                  <Trade
                  // changePage={changePage}
                  // sideBar={sideBar}
                  // setSideBar={setSideBar}
                  />
                }
              />
              <Route path="*" element={<Navigate to="/chat" replace />} />
            </Routes>
          </div>
        </ChatsProvider>
      </UserProvider>
    </div>
  );
}

export default App;
