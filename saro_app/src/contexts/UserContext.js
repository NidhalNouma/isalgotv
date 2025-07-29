import { createContext, useContext, useState, useEffect } from "react";

const UserContext = createContext();

export const UserProvider = ({ children }) => {
  const [user, setUser] = useState(undefined);
  const [tokens, setTokens] = useState({
    availabel: 0,
    free: 0,
  });

  const updateTokens = (free, availabel) => {
    setTokens((prevTokens) => ({
      availabel,
      free,
    }));
  };

  useEffect(() => {
    const context = window.__SARO_CONTEXT__;

    let user =
      context.user.email !== "None"
        ? {
            email: context.user.email,
            id: context.user.id,
            tradingviewUsername: context.user.tvUsername,
            isLifetime: context.user.isLifetime === "True",
            hasSubscription: context.user.hasSubscription === "True",
            subscriptionPlan: context.user.subscriptionPlan,
          }
        : null;

    console.log("user ...", user);

    setUser(user);

    if (context?.tokens)
      setTokens({
        availabel: parseInt(context.tokens.aiTokensAvailable, 10) || 0,
        free: parseInt(context.tokens.aiFreeTokens, 10) || 0,
      });
  }, []);

  return (
    <UserContext.Provider value={{ user, tokens, updateTokens }}>
      {children}
    </UserContext.Provider>
  );
};

export const useUser = () => useContext(UserContext);
