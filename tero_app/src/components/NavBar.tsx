import React, { Fragment } from "react";

interface NavbarProps {
  className?: string;
  onMenuClick?: () => void;
  onMenuHover?: () => void;
  page?: string;
  changePage?: (page: string) => void;
  setSideBar: (open: boolean) => void;
}

const Navbar: React.FC<NavbarProps> = ({ className, setSideBar }) => {
  return (
    <Fragment>
      <nav
        className={
          "md:hidden flex nav-bg from-text/10 items-center justify-between absolute left-0 right-0 rounded-t-xl top-0 z-30 py-2 px-3" +
          className
        }
      >
        <div className="flex items-center gap-1.5">
          <button
            onClick={() => setSideBar(true)}
            className={`p-2 btn-icon rounded-md transition-colors md:hidden`}
            aria-label="Toggle Sidebar"
          >
            <svg
              className="h-4 aspect-auto fill-current"
              viewBox="0 0 20 20"
              xmlns="http://www.w3.org/2000/svg"
            >
              <path d="M11.6663 12.6686L11.801 12.6823C12.1038 12.7445 12.3313 13.0125 12.3313 13.3337C12.3311 13.6547 12.1038 13.9229 11.801 13.985L11.6663 13.9987H3.33325C2.96609 13.9987 2.66839 13.7008 2.66821 13.3337C2.66821 12.9664 2.96598 12.6686 3.33325 12.6686H11.6663ZM16.6663 6.00163L16.801 6.0153C17.1038 6.07747 17.3313 6.34546 17.3313 6.66667C17.3313 6.98788 17.1038 7.25586 16.801 7.31803L16.6663 7.33171H3.33325C2.96598 7.33171 2.66821 7.03394 2.66821 6.66667C2.66821 6.2994 2.96598 6.00163 3.33325 6.00163H16.6663Z"></path>
            </svg>
          </button>

          <div className=" flex justify-center items-center gap-3 ">
            {/* <button
              className={`px-2 py-0.5 gap-1 btn-icon rounded-full transition-colors ${
                page === "chat" &&
                "text-background hover:text-background bg-title"
              } `}
              aria-label="Close Session"
              onClick={() => changePage("chat")}
            >
              <MessagesSquare className="w-4 aspect-auto " />
            </button>
            <button
              className={`px-2 py-0.5 gap-1 btn-icon rounded-full transition-colors  ${
                page === "trade" &&
                "text-background hover:text-background bg-title"
              } `}
              aria-label="Close Session"
              onClick={() => changePage("trade")}
            >
              <Activity className="w-4 aspect-auto " />
            </button> */}
          </div>
        </div>
      </nav>
    </Fragment>
  );
};

export default Navbar;
