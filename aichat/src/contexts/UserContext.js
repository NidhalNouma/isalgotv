import { createContext, useContext, useState, useEffect } from "react";

const UserContext = createContext();

export const UserProvider = ({ children }) => {
  const [user, setUser] = useState(undefined);

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
  }, []);

  return (
    <UserContext.Provider value={{ user }}>{children}</UserContext.Provider>
  );
};

export const useUser = () => useContext(UserContext);
