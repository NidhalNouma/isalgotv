import { Fragment, useEffect, useState, useRef } from "react";
import {
  Search,
  MessageSquarePlus,
  MessagesSquare,
  Activity,
  PanelLeft,
  PanelRight,
  X,
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

import { ScrollDiv } from "./ui/ScrollableContainer";

import { useChat } from "../contexts/ChatsContext";
import { useUser } from "../contexts/UserContext";

import HrefButton from "./ui/hrefButton";

import { HOST } from "../constant";

function SideBar({ onClose, open, setOpen, page, changePage }) {
  const [renderOpen, setRenderOpen] = useState(false);

  const [isMobile, setIsMobile] = useState(false);
  useEffect(() => {
    const handleResize = () => setIsMobile(window.innerWidth <= 768);
    handleResize();
    window.addEventListener("resize", handleResize);
    return () => window.removeEventListener("resize", handleResize);
  }, []);

  useEffect(() => {
    if (open) setRenderOpen(true);
    else if (isMobile) setRenderOpen(open);
  }, [open]);

  // Mobile drawer sidebar
  if (isMobile) {
    return (
      <Fragment>
        <AnimatePresence>
          {open && (
            <motion.div
              className="absolute inset-0 z-40 flex"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
            >
              {/* Overlay backdrop */}
              <div
                className="absolute inset-0 bg-background bg-opacity-60"
                onClick={() => setOpen(false)}
              />
              {/* Sliding drawer */}
              <motion.div
                className="relative w-52 px-2 py-4 space-y-2 h-full backdrop-blur-3xl bg-text/10 flex flex-col rounded-r-xl md:hidden"
                initial={{ x: "-100%" }}
                animate={{ x: 0 }}
                exit={{ x: "-100%" }}
                transition={{ duration: 0.2, ease: "easeInOut" }}
              >
                <FullSideBar
                  onClose={onClose}
                  open={open}
                  setOpen={setOpen}
                  page={page}
                  changePage={changePage}
                />
              </motion.div>
            </motion.div>
          )}
        </AnimatePresence>
      </Fragment>
    );
  }
  return (
    <motion.div
      initial={false}
      animate={{ width: open ? 240 : 48 }}
      transition={{ duration: 0.22, ease: open ? "easeIn" : "easeOut" }}
      onAnimationComplete={() => {
        if (!open) setRenderOpen(false);
      }}
      className={` overflow-hidden space-y-2 py-4 px-2 backdrop-blur-[320px] bg-text/10 rounded-xl h-full hidden md:flex flex-col relative`}
    >
      {!renderOpen ? (
        <MinSideBar
          onClose={onClose}
          open={open}
          setOpen={setOpen}
          page={page}
          changePage={changePage}
        />
      ) : (
        <FullSideBar
          onClose={onClose}
          open={open}
          setOpen={setOpen}
          page={page}
          changePage={changePage}
        />
      )}
    </motion.div>
  );
}

export default SideBar;

function MinSideBar({ onClose, open, setOpen, page, changePage }) {
  const { chats, createNewChat, isTyping, retrieveChats, currentChat } =
    useChat();

  const { user } = useUser();

  const [hideLogo, setHideLogo] = useState(false);

  return (
    <Fragment>
      <button
        onClick={() => setOpen(true)}
        onMouseEnter={() => setHideLogo(true)}
        onMouseLeave={() => setHideLogo(false)}
        className="cursor-e-resize btn-icon transition-colors ml-auto mr-auto mb-1"
      >
        {hideLogo ? (
          <PanelLeft className="h-5 aspect-auto" />
        ) : (
          <Logo className="h-5" />
        )}
      </button>
      <button
        className={` px-2 py-1 btn-icon ml-auto mr-auto rounded-md transition-colors ${
          page === "chat" && "text-background hover:text-background bg-title"
        }`}
        aria-label="Chat"
        onClick={() => changePage("chat")}
      >
        <MessagesSquare className="w-3.5 aspect-auto " />
      </button>
      <button
        className={` px-2 py-1 btn-icon ml-auto mr-auto rounded-md transition-colors ${
          page === "trade" && "text-background hover:text-background bg-title"
        }`}
        aria-label="Trade"
        onClick={() => changePage("trade")}
      >
        <Activity className="w-3.5 aspect-auto" />
      </button>

      {page === "chat" && (
        <button
          disabled={!currentChat}
          onClick={() => {
            createNewChat();
          }}
          className="px-2 py-1 btn-icon ml-auto mr-auto rounded-md transition-colors "
          aria-label="New Chat"
        >
          <MessageSquarePlus className="w-3.5 aspect-auto flex-shrink-0" />
        </button>
      )}

      {page === "trade" && (
        <button
          disabled={!currentChat}
          onClick={() => {
            createNewChat();
          }}
          className="px-2 py-2 btn-icon ml-auto mr-auto rounded-md transition-colors "
          aria-label="New Chat"
        >
          <svg
            className="w-3.5 aspect-auto flex-shrink-0 stroke-current "
            viewBox="0 0 22 22"
            fill="none"
            xmlns="http://www.w3.org/2000/svg"
          >
            <path
              d="M21 11H18.52C18.083 10.9991 17.6577 11.1413 17.3091 11.405C16.9606 11.6686 16.708 12.0392 16.59 12.46L14.24 20.82C14.2249 20.8719 14.1933 20.9175 14.15 20.95C14.1067 20.9825 14.0541 21 14 21C13.9459 21 13.8933 20.9825 13.85 20.95C13.8067 20.9175 13.7751 20.8719 13.76 20.82L8.24 1.18C8.22485 1.12807 8.19327 1.08246 8.15 1.05C8.10673 1.01754 8.05409 1 8 1C7.94591 1 7.89327 1.01754 7.85 1.05C7.80673 1.08246 7.77515 1.12807 7.76 1.18L5.41 9.54C5.29246 9.95915 5.04138 10.3285 4.69486 10.592C4.34835 10.8555 3.92532 10.9988 3.49 11H1"
              stroke-width="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
            <path
              d="M18.4971 1L18.4971 6.71429"
              strokeWidth="2"
              strokeLinecap="round"
            />
            <path
              d="M16 3.85742L21 3.85742"
              strokeWidth="2"
              strokeLinecap="round"
            />
          </svg>
        </button>
      )}

      <div
        onClick={(e) => {
          setOpen(true);
        }}
        className="cursor-e-resize grow overflow-y-auto no-scrollbar"
      ></div>
      {user && (
        <Fragment>
          <button
            className={`mt-auto !mb-1 px-2 py-1 btn-icon ml-auto mr-auto rounded-md transition-colors `}
            onClick={() => window.buyAiToken()}
          >
            <svg
              className="w-3.5 aspect-auto"
              xmlns="http://www.w3.org/2000/svg"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <circle cx="8" cy="8" r="6"></circle>
              <path d="M18.09 10.37A6 6 0 1 1 10.34 18"></path>
              <path d="M7 6h1v4"></path>
              <path d="m16.71 13.88.7.71-2.82 2.82"></path>
            </svg>
          </button>
          <a
            href={HOST + "/my/settings/"}
            className={`px-2 py-1 !mb-1 btn-icon ml-auto mr-auto rounded-md transition-colors `}
          >
            <svg
              className="h-3.5 aspect-auto"
              stroke="currentColor"
              fill="currentColor"
              strokeWidth="0"
              viewBox="0 0 512 512"
              xmlns="http://www.w3.org/2000/svg"
            >
              <path
                fill="none"
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth="32"
                d="M262.29 192.31a64 64 0 1 0 57.4 57.4 64.13 64.13 0 0 0-57.4-57.4zM416.39 256a154.34 154.34 0 0 1-1.53 20.79l45.21 35.46a10.81 10.81 0 0 1 2.45 13.75l-42.77 74a10.81 10.81 0 0 1-13.14 4.59l-44.9-18.08a16.11 16.11 0 0 0-15.17 1.75A164.48 164.48 0 0 1 325 400.8a15.94 15.94 0 0 0-8.82 12.14l-6.73 47.89a11.08 11.08 0 0 1-10.68 9.17h-85.54a11.11 11.11 0 0 1-10.69-8.87l-6.72-47.82a16.07 16.07 0 0 0-9-12.22 155.3 155.3 0 0 1-21.46-12.57 16 16 0 0 0-15.11-1.71l-44.89 18.07a10.81 10.81 0 0 1-13.14-4.58l-42.77-74a10.8 10.8 0 0 1 2.45-13.75l38.21-30a16.05 16.05 0 0 0 6-14.08c-.36-4.17-.58-8.33-.58-12.5s.21-8.27.58-12.35a16 16 0 0 0-6.07-13.94l-38.19-30A10.81 10.81 0 0 1 49.48 186l42.77-74a10.81 10.81 0 0 1 13.14-4.59l44.9 18.08a16.11 16.11 0 0 0 15.17-1.75A164.48 164.48 0 0 1 187 111.2a15.94 15.94 0 0 0 8.82-12.14l6.73-47.89A11.08 11.08 0 0 1 213.23 42h85.54a11.11 11.11 0 0 1 10.69 8.87l6.72 47.82a16.07 16.07 0 0 0 9 12.22 155.3 155.3 0 0 1 21.46 12.57 16 16 0 0 0 15.11 1.71l44.89-18.07a10.81 10.81 0 0 1 13.14 4.58l42.77 74a10.8 10.8 0 0 1-2.45 13.75l-38.21 30a16.05 16.05 0 0 0-6.05 14.08c.33 4.14.55 8.3.55 12.47z"
              ></path>
            </svg>
          </a>
        </Fragment>
      )}
      <a
        href={HOST}
        className={`px-2 py-1 !mb-1 btn-icon ml-auto mr-auto rounded-md transition-colors `}
      >
        <svg
          className="h-3.5 aspect-auto"
          stroke="currentColor"
          fill="none"
          strokeWidth="2"
          viewBox="0 0 24 24"
          strokeLinecap="round"
          strokeLinejoin="round"
          xmlns="http://www.w3.org/2000/svg"
        >
          <path stroke="none" d="M0 0h24v24H0z" fill="none"></path>
          <path d="M10 8v-2a2 2 0 0 1 2 -2h7a2 2 0 0 1 2 2v12a2 2 0 0 1 -2 2h-7a2 2 0 0 1 -2 -2v-2"></path>
          <path d="M15 12h-12l3 -3"></path>
          <path d="M6 15l-3 -3"></path>
        </svg>
      </a>
    </Fragment>
  );
}

function FullSideBar({ onClose, open, setOpen, page, changePage }) {
  const { chats, createNewChat, isTyping, retrieveChats, currentChat } =
    useChat();

  const { user } = useUser();

  const [searchQuery, setSearchQuery] = useState("");
  const [filteredChats, setFilteredChats] = useState([]);

  useEffect(() => {
    if (searchQuery.length > 0) {
      let fChats = chats.filter((chat) =>
        chat.title?.toLowerCase().includes(searchQuery.toLowerCase())
      );
      setFilteredChats(fChats);
    } else setFilteredChats([...chats]);
  }, [chats, searchQuery]);

  return (
    <Fragment>
      <div className="flex items-center justify-between mb-1">
        <a className="btn-icon ml-0" href="/">
          <Logo className="h-5" />
        </a>
        <button
          onClick={() => setOpen(false)}
          className="btn-icon cursor-w-resize transition-colors ml-auto"
        >
          <PanelLeft className="h-5 aspect-auto hidden md:block" />
          <X className="h-5 aspect-auto block md:hidden" />
        </button>
      </div>
      <button
        className={`px-2 py-1 gap-1 btn-icon rounded-md transition-colors w-full max-w-xs ${
          page === "chat" && "text-background hover:text-background bg-title"
        }`}
        aria-label="Chat"
        onClick={() => changePage("chat")}
      >
        <MessagesSquare className="w-3.5 aspect-auto" />
        Chat
      </button>
      <button
        className={`px-2 py-1 gap-1 btn-icon rounded-md transition-colors w-full max-w-xs ${
          page === "trade" && "text-background hover:text-background bg-title"
        }`}
        aria-label="Trade"
        onClick={() => changePage("trade")}
      >
        <Activity className="w-3.5 aspect-auto" />
        Trade
      </button>
      {page === "chat" && (
        <button
          disabled={!currentChat}
          onClick={() => {
            createNewChat();
          }}
          className="px-2 py-1 gap-1 btn-icon rounded-md transition-colors w-full max-w-xs "
          aria-label="New Chat"
        >
          <MessageSquarePlus className="w-3.5 aspect-auto flex-shrink-0" />
          <span className="truncate ">New Chat</span>
        </button>
      )}
      {page === "trade" && (
        <button
          disabled={!currentChat}
          onClick={() => {
            createNewChat();
          }}
          className="px-2 py-1 gap-1 btn-icon rounded-md transition-colors w-full max-w-xs "
          aria-label="New Chat"
        >
          <svg
            className="w-3.5 aspect-auto flex-shrink-0 stroke-current "
            viewBox="0 0 22 22"
            fill="none"
            xmlns="http://www.w3.org/2000/svg"
          >
            <path
              d="M21 11H18.52C18.083 10.9991 17.6577 11.1413 17.3091 11.405C16.9606 11.6686 16.708 12.0392 16.59 12.46L14.24 20.82C14.2249 20.8719 14.1933 20.9175 14.15 20.95C14.1067 20.9825 14.0541 21 14 21C13.9459 21 13.8933 20.9825 13.85 20.95C13.8067 20.9175 13.7751 20.8719 13.76 20.82L8.24 1.18C8.22485 1.12807 8.19327 1.08246 8.15 1.05C8.10673 1.01754 8.05409 1 8 1C7.94591 1 7.89327 1.01754 7.85 1.05C7.80673 1.08246 7.77515 1.12807 7.76 1.18L5.41 9.54C5.29246 9.95915 5.04138 10.3285 4.69486 10.592C4.34835 10.8555 3.92532 10.9988 3.49 11H1"
              stroke-width="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
            <path
              d="M18.4971 1L18.4971 6.71429"
              strokeWidth="2"
              strokeLinecap="round"
            />
            <path
              d="M16 3.85742L21 3.85742"
              strokeWidth="2"
              strokeLinecap="round"
            />
          </svg>
          <span className="truncate ">New Task</span>
        </button>
      )}
      <section className="grow overflow-y-auto no-scrollbar">
        {page === "chat" && (
          <Fragment>
            {chats.length > 0 && (
              <div className="relative my-2 mx-0.5">
                <input
                  type="text"
                  placeholder="Search chats..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full input-text py-1 pl-9 pr-3"
                />
                <Search className="absolute left-2.5 top-2 w-4 h-4 text-text/60" />
              </div>
            )}

            <ScrollDiv
              className="space-y-2 px-2 box-content"
              onBottomReach={retrieveChats}
            >
              {filteredChats.length > 0 && (
                <h6 className="text-text/80 text-sm pt-3 pb-2">Chats</h6>
              )}
              {chats &&
                filteredChats.map((chat) => (
                  <HrefButton key={chat.id} chat={chat} onClose={onClose} />
                ))}
            </ScrollDiv>
          </Fragment>
        )}
      </section>
      {user && (
        <Fragment>
          <button
            className={`px-2 py-1 gap-1 btn-icon rounded-md transition-colors w-full max-w-xs`}
            onClick={() => window.buyAiToken()}
          >
            <svg
              className="w-3.5 aspect-auto"
              xmlns="http://www.w3.org/2000/svg"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <circle cx="8" cy="8" r="6"></circle>
              <path d="M18.09 10.37A6 6 0 1 1 10.34 18"></path>
              <path d="M7 6h1v4"></path>
              <path d="m16.71 13.88.7.71-2.82 2.82"></path>
            </svg>
            Tokens
          </button>
          <a
            href={HOST + "/my/settings/"}
            className={`px-2 py-1 gap-1 btn-icon rounded-md transition-colors w-full max-w-xs `}
            aria-label="Trade"
          >
            <svg
              className="h-3.5 aspect-auto"
              stroke="currentColor"
              fill="currentColor"
              strokeWidth="0"
              viewBox="0 0 512 512"
              xmlns="http://www.w3.org/2000/svg"
            >
              <path
                fill="none"
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth="32"
                d="M262.29 192.31a64 64 0 1 0 57.4 57.4 64.13 64.13 0 0 0-57.4-57.4zM416.39 256a154.34 154.34 0 0 1-1.53 20.79l45.21 35.46a10.81 10.81 0 0 1 2.45 13.75l-42.77 74a10.81 10.81 0 0 1-13.14 4.59l-44.9-18.08a16.11 16.11 0 0 0-15.17 1.75A164.48 164.48 0 0 1 325 400.8a15.94 15.94 0 0 0-8.82 12.14l-6.73 47.89a11.08 11.08 0 0 1-10.68 9.17h-85.54a11.11 11.11 0 0 1-10.69-8.87l-6.72-47.82a16.07 16.07 0 0 0-9-12.22 155.3 155.3 0 0 1-21.46-12.57 16 16 0 0 0-15.11-1.71l-44.89 18.07a10.81 10.81 0 0 1-13.14-4.58l-42.77-74a10.8 10.8 0 0 1 2.45-13.75l38.21-30a16.05 16.05 0 0 0 6-14.08c-.36-4.17-.58-8.33-.58-12.5s.21-8.27.58-12.35a16 16 0 0 0-6.07-13.94l-38.19-30A10.81 10.81 0 0 1 49.48 186l42.77-74a10.81 10.81 0 0 1 13.14-4.59l44.9 18.08a16.11 16.11 0 0 0 15.17-1.75A164.48 164.48 0 0 1 187 111.2a15.94 15.94 0 0 0 8.82-12.14l6.73-47.89A11.08 11.08 0 0 1 213.23 42h85.54a11.11 11.11 0 0 1 10.69 8.87l6.72 47.82a16.07 16.07 0 0 0 9 12.22 155.3 155.3 0 0 1 21.46 12.57 16 16 0 0 0 15.11 1.71l44.89-18.07a10.81 10.81 0 0 1 13.14 4.58l42.77 74a10.8 10.8 0 0 1-2.45 13.75l-38.21 30a16.05 16.05 0 0 0-6.05 14.08c.33 4.14.55 8.3.55 12.47z"
              ></path>
            </svg>
            Settings
          </a>
        </Fragment>
      )}
      <a
        href={HOST}
        className={`px-2 py-1 gap-1 btn-icon rounded-md transition-colors w-full max-w-xs `}
      >
        <svg
          className="h-3.5 aspect-auto"
          stroke="currentColor"
          fill="none"
          strokeWidth="2"
          viewBox="0 0 24 24"
          strokeLinecap="round"
          strokeLinejoin="round"
          xmlns="http://www.w3.org/2000/svg"
        >
          <path stroke="none" d="M0 0h24v24H0z" fill="none"></path>
          <path d="M10 8v-2a2 2 0 0 1 2 -2h7a2 2 0 0 1 2 2v12a2 2 0 0 1 -2 2h-7a2 2 0 0 1 -2 -2v-2"></path>
          <path d="M15 12h-12l3 -3"></path>
          <path d="M6 15l-3 -3"></path>
        </svg>
        IsAlgo
      </a>
    </Fragment>
  );
}

function Logo({ className }) {
  return (
    <svg
      className={`${className} aspect-auto fill-title stroke-title hover:fill-title/80 hover:stroke-title/80 transition-colors`}
      viewBox="0 0 302 428"
      xmlns="http://www.w3.org/2000/svg"
    >
      <path
        d="M211.404 5L211.404 102.073"
        strokeWidth="10"
        strokeLinecap="round"
      />
      <path
        d="M203.638 82.6582H219.169C222.029 82.6582 224.346 86.1351 224.346 90.4241V152.551C224.346 156.84 222.029 160.317 219.169 160.317H203.638C200.778 160.317 198.46 156.84 198.46 152.551V90.4241C198.46 86.1351 200.778 82.6582 203.638 82.6582Z"
        strokeWidth="15"
      />
      <path
        d="M97.9228 350.173L82.7244 349.97C79.9265 349.933 77.6832 346.437 77.7139 342.161L78.1584 280.231C78.1891 275.955 80.4821 272.52 83.28 272.557L98.4784 272.76C101.276 272.797 103.52 276.293 103.489 280.568L103.044 342.499C103.014 346.774 100.721 350.21 97.9228 350.173Z"
        strokeWidth="15"
      />
      <path
        d="M90.3241 351.011L90.3241 422.421"
        strokeWidth="10"
        strokeWinecap="round"
      />
      <path d="M18.9213 127.582C8.02681 137.789 1.78067 149.872 0.340851 164.059C-1.57142 182.902 4.55596 199.113 18.891 212.921C28.9832 222.643 41.8664 227.94 55.3822 232.327C79.6901 240.217 103.996 248.113 128.336 255.922C130.624 256.656 131.54 257.591 131.405 259.867C131.223 262.953 131.671 266.065 131.675 269.165C131.712 299.984 131.668 330.803 131.776 361.621C131.792 366.107 131.763 370.283 127.277 373.366C125.943 374.283 125.182 375.95 124.33 377.359C118.441 387.094 118.719 396.922 125.082 406.204C131.337 415.328 141.054 419.725 152.872 419.122C165.618 418.471 174.737 412.28 179.426 401.673C184.272 390.709 182.071 380.394 173.3 371.557C170.91 369.149 169.839 366.819 169.846 363.592C169.937 321.504 169.835 279.416 169.988 237.328C170.003 233.42 168.546 231.761 164.564 230.464C132.124 219.898 99.77 209.118 67.3868 198.411C62.832 196.905 58.3622 195.258 54.4411 192.602C34.1485 178.855 39.3168 156.014 56.0194 147.657C69.4852 140.919 82.4802 133.417 95.746 126.349C97.8978 125.202 98.6712 123.823 98.6535 121.617C98.5638 110.463 98.6334 99.3077 98.6097 88.1532C98.5995 83.3534 97.7505 82.8281 93.2104 85.2459C77.7509 93.4787 62.3417 101.789 46.9502 110.125C37.3547 115.323 27.3506 119.996 18.9213 127.582ZM291.176 226.931C289.203 224.537 287.366 222.067 285.166 219.809C274.858 209.231 261.201 203.678 246.992 199.036C223.188 191.259 199.337 183.597 175.439 176.058C171.381 174.778 169.753 173.074 169.79 168.94C170.034 141.693 169.928 114.444 169.929 87.195C169.929 83.8617 170.019 80.522 169.822 77.1971C169.676 74.7372 168.413 73.5887 165.52 74.9425C155.903 79.4432 146.289 79.4173 136.631 74.9188C132.786 73.1273 131.39 73.9797 131.27 78.0217C131.178 81.118 131.268 84.2188 131.283 87.3175C131.453 123.414 131.67 159.511 131.714 195.608C131.718 198.814 132.931 200.24 136.191 201.305C169.568 212.212 202.732 223.647 236.295 234.091C240.398 235.367 244.459 236.822 247.948 239.174C256.886 245.199 261.385 253.059 259.685 263.345C258.338 271.492 252.969 277.111 245.54 281.254C232.329 288.619 219.037 295.868 205.685 303.021C203.046 304.434 201.994 306.086 202.024 308.822C202.145 319.973 202.059 331.126 202.098 342.279C202.103 343.592 201.53 345.285 203.241 346.007C204.822 346.674 206.098 345.432 207.39 344.754C227.204 334.368 246.942 323.861 266.839 313.607C301.494 295.748 312.378 257.863 291.176 226.931Z" />
      <circle cx="151.003" cy="43.8285" r="21.5721" />
    </svg>
  );
}
