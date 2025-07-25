import { createContext, useContext, useState, useEffect } from "react";

const UserContext = createContext();

export const UserProvider = ({ children }) => {
  const [user, setUser] = useState(undefined);
  const [tokens, setTokens] = useState({
    availabel: 0,
    free: 0,
  });

  useEffect(() => {
    const rootDiv = document.getElementById("saro");
    const email = rootDiv.getAttribute("user-email");
    const id = rootDiv.getAttribute("user-id");
    const tradingviewUsername = rootDiv.getAttribute("user-tv-username");
    const isLifetime = rootDiv.getAttribute("user-is-lifetime");
    const hasSubscription = rootDiv.getAttribute("user-has-subscription");
    const subscriptionPlan = rootDiv.getAttribute("user-subscription-plan");

    let user =
      email !== "None"
        ? {
            email,
            id,
            tradingviewUsername,
            isLifetime: isLifetime === "True",
            hasSubscription: hasSubscription === "True",
            subscriptionPlan,
          }
        : null;

    console.log("user ...", user);

    setUser(user);

    const availabelTokens = rootDiv.getAttribute("available-tokens");
    const freeTokens = rootDiv.getAttribute("free-tokens");

    setTokens({
      availabel: availabelTokens ? parseInt(availabelTokens, 10) : 0,
      free: freeTokens ? parseInt(freeTokens, 10) : 0,
    });
  }, []);

  return (
    <UserContext.Provider value={{ user, tokens }}>
      {children}
    </UserContext.Provider>
  );
};

export const useUser = () => useContext(UserContext);
