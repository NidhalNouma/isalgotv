import { useState, useEffect } from "react";
import { useUser } from "../contexts/UserContext";

import type { Account } from "../types/user";

export function NewTaskHook(): {
  step: number;
  nextStep: (s?: number | null) => void;
  accounts: Account[];
  selectedAccount: Account | null;
  setSelectedAccount: React.Dispatch<React.SetStateAction<Account | null>>;
} {
  const { accounts, getAccounts } = useUser();

  const [step, setStep] = useState<number>(1);
  const [selectedAccount, setSelectedAccount] = useState<Account | null>(null);

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
