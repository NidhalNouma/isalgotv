import { Fragment } from "react";
import Navbar from "./components/navbar";

import { UserProvider, useUser } from "./contexts/UserContext";
import HeroSection from "./components/HeroSection2";

function App() {
  return (
    <UserProvider>
      <Navbar className="mx-4 pb-4 pt-6" />
      <div className="p-4 relative flex flex-col grow w-full overflow-y-scroll scrollbar-hide">
        <Main />
      </div>
    </UserProvider>
  );
}

export default App;

function Main() {
  const { user } = useUser();

  return user ? (
    <Fragment>
      <div className="text-title max-w-5xl mx-auto my-auto text-center py-16">
        <h1 className="text-4xl sm:text-5xl font-medium mb-6 tracking-tight leading-tight ">
          <span className="bg-gradient-to-r from-accent via-primary/70 to-primary bg-clip-text text-transparent animate-gradient-x">
            IsalGo AI
          </span>{" "}
          is coming soon!
        </h1>
      </div>
    </Fragment>
  ) : (
    <Fragment>
      <HeroSection />
    </Fragment>
  );
}
