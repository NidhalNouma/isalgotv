import { useState, Fragment } from "react";
import Navbar from "../components/NavBar";
import SideBar from "../components/SideBar";
import TradeSection from "../components/TradeSection";

import { ChatsProvider } from "../contexts/ChatsContext";

const rootDiv = document.getElementById("saro");
const isPage = rootDiv.getAttribute("is-page") === "true" ? true : false;

function Trade({ changePage, sideBar, setSideBar }) {
  return (
    <div className="flex h-screen max-h-screen">
      {isPage && (
        <SideBar
          page="trade"
          changePage={changePage}
          open={sideBar}
          setOpen={setSideBar}
        />
      )}
      <div className="px-4 relative flex flex-col w-full flex-grow overflow-y-scroll scrollbar-hide">
        <Navbar className="" page="trade" changePage={changePage} />
        <TradeSection />
      </div>
    </div>
  );
}

export default Trade;
