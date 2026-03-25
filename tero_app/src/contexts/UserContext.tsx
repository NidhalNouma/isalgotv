import React, {
  createContext,
  useContext,
  useState,
  useEffect,
  type ReactNode,
} from "react";

import { type AIModel } from "../types/user";
import type { User, Tokens } from "../types/user";
import { fetchAccounts } from "../api/trade";

import type { Account } from "../types/user";

interface UserContextValue {
  user: User | null | undefined;
  tokens: Tokens;
  updateTokens: (free: number, availabel: number) => void;
  getAccounts: () => void;
  accounts: Account[];
}

const UserContext = createContext<UserContextValue | undefined>(undefined);

// Local fallback types for window.__TERO_CONTEXT__ in case global ambient type isn't picked up

interface TeroContextRaw {
  models?: AIModel[];
  user?: User;
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

  const [accounts, setAccounts] = useState<Account[]>([]);

  const getAccounts = () => {
    fetchAccounts().then((data: any) => {
      const accs = data?.accounts;
      setAccounts(accs);
    });
  };

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
            tradingviewUsername: ctx.user.tradingviewUsername,
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

    getAccounts();
  }, []);

  return (
    <UserContext.Provider
      value={{ user, tokens, updateTokens, getAccounts, accounts }}
    >
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
