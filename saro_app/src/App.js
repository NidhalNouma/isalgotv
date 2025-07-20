import { Fragment, useState } from "react";
import {
  Routes,
  Route,
  useLocation,
  useNavigate,
  Navigate,
} from "react-router-dom";
import Chat from "./pages/Chat";
import Trade from "./pages/Trade";

import { UserProvider } from "./contexts/UserContext";
import { ChatsProvider } from "./contexts/ChatsContext";

import SideBar from "./components/SideBar";

function App() {
  const [sideBar, setSideBar] = useState(false);

  const navigate = useNavigate();
  const { pathname } = useLocation();
  const page = pathname.includes("trade")
    ? "trade"
    : pathname.includes("chat")
    ? "chat"
    : "";
  const changePage = (newPage) => {
    navigate(newPage === "trade" ? "/trade" : "/chat");
  };

  return (
    <div className="relative flex h-full max-h-screen overflow-hidden bg-text/10 rounded-xl">
      <UserProvider>
        <ChatsProvider>
          <SideBar
            page={page}
            changePage={changePage}
            open={sideBar}
            setOpen={setSideBar}
          />
          <Routes>
            <Route
              path="/chat"
              element={
                <Chat
                  changePage={changePage}
                  sideBar={sideBar}
                  setSideBar={setSideBar}
                />
              }
            />
            <Route
              path="/trade"
              element={
                <Trade
                  changePage={changePage}
                  sideBar={sideBar}
                  setSideBar={setSideBar}
                />
              }
            />
            <Route path="*" element={<Navigate to="/chat" replace />} />
          </Routes>
        </ChatsProvider>
      </UserProvider>
    </div>
  );
}

export default App;
