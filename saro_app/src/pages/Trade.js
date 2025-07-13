import { useState, Fragment } from "react";
import Navbar from "../components/NavBar";
import TradeSection from "../components/TradeSection";

function Trade({ changePage, sideBar, setSideBar }) {
  return (
    <div className="px-4 relative flex flex-col w-full flex-grow max-h-full overflow-hidden scrollbar-hide">
      <Navbar
        className=""
        page="trade"
        changePage={changePage}
        setSideBar={setSideBar}
      />
      <TradeSection />
    </div>
  );
}

export default Trade;
