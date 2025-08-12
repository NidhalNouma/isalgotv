import React, {
  createContext,
  useContext,
  useState,
  useEffect,
  type ReactNode,
} from "react";
import { type AIModel } from "../constant";

export interface User {
  email: string;
  id: number | string;
  tradingviewUsername: string;
  isLifetime: boolean;
  hasSubscription: boolean;
  subscriptionPlan: string;
}

export interface Tokens {
  availabel: number;
  free: number;
}

interface UserContextValue {
  user: User | null | undefined;
  tokens: Tokens;
  updateTokens: (free: number, availabel: number) => void;
}

const UserContext = createContext<UserContextValue | undefined>(undefined);

// Local fallback types for window.__TERO_CONTEXT__ in case global ambient type isn't picked up
interface TeroUserRaw {
  email: string;
  id: number | string;
  tvUsername: string;
  isLifetime: string;
  hasSubscription: string;
  subscriptionPlan: string;
}
interface TeroContextRaw {
  models?: AIModel[];
  user?: TeroUserRaw;
  tokens?: {
    aiTokensAvailable?: string;
    aiFreeTokens?: string;
  };
}

interface UserProviderProps {
  children: ReactNode;
}

export const UserProvider: React.FC<UserProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null | undefined>(undefined);
  const [tokens, setTokens] = useState<Tokens>({
    availabel: 0,
    free: 0,
  });

  const updateTokens = (free: number, availabel: number) => {
    setTokens({ availabel, free });
  };

  useEffect(() => {
    const ctx = (window as unknown as { __TERO_CONTEXT__?: TeroContextRaw })
      .__TERO_CONTEXT__;
    if (!ctx) return;

    const userObj: User | null =
      ctx?.user && ctx.user.email !== "None"
        ? {
            email: ctx.user.email,
            id: ctx.user.id,
            tradingviewUsername: ctx.user.tvUsername,
            isLifetime: ctx.user.isLifetime === "True",
            hasSubscription: ctx.user.hasSubscription === "True",
            subscriptionPlan: ctx.user.subscriptionPlan,
          }
        : null;

    console.log("user ...", userObj);

    setUser(userObj);

    if (ctx.tokens) {
      setTokens({
        availabel: parseInt(ctx.tokens.aiTokensAvailable ?? "0", 10) || 0,
        free: parseInt(ctx.tokens.aiFreeTokens ?? "0", 10) || 0,
      });
    }
  }, []);

  return (
    <UserContext.Provider value={{ user, tokens, updateTokens }}>
      {children}
    </UserContext.Provider>
  );
};

export const useUser = (): UserContextValue => {
  const ctx = useContext(UserContext);
  if (!ctx) {
    throw new Error("useUser must be used within a UserProvider");
  }
  return ctx;
};
