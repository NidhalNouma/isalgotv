import { Fragment, useState } from "react";
import Chat from "./pages/Chat";
import Trade from "./pages/Trade";

import { UserProvider } from "./contexts/UserContext";
import { ChatsProvider } from "./contexts/ChatsContext";

function App() {
  const [page, setPage] = useState("chat");

  return (
    <UserProvider>
      <ChatsProvider>
        {page === "chat" ? (
          <Chat changePage={setPage} />
        ) : page === "trade" ? (
          <Trade changePage={setPage} />
        ) : (
          <Fragment />
        )}
      </ChatsProvider>
    </UserProvider>
  );
}

export default App;
