import { useState, useEffect } from "react";
import { fetchAccounts } from "../api/trade";

import type { Account } from "../types/user";

export function NewTaskHook(): {
  step: number;
  nextStep: (s?: number | null) => void;
  accounts: Account[];
  selectedAccount: Account | null;
  setSelectedAccount: React.Dispatch<React.SetStateAction<Account | null>>;
} {
  const [step, setStep] = useState<number>(1);
  const [accounts, setAccounts] = useState<Account[]>([]);

  const [selectedAccount, setSelectedAccount] = useState<Account | null>(null);

  function getAccounts() {
    fetchAccounts().then((data: any) => {
      const cryptoAccounts = data?.crypto_accounts;
      const forexAccounts = data?.forex_accounts;
      console.log(cryptoAccounts, forexAccounts);
      setAccounts([...cryptoAccounts, ...forexAccounts]);
    });
  }

  useEffect(() => {
    if (step === 1) getAccounts();
  }, [step]);

  function nextStep(s: number | null = null) {
    if (!s) {
      if (step >= 3) return;
      setStep((prev) => prev + 1);
    }

    if (s) {
      if (s > 3 || s < 1) return;

      setStep(s);
    }
  }

  return {
    step,
    nextStep,
    accounts,
    selectedAccount,
    setSelectedAccount,
  };
}
