import { useState, useEffect } from "react";
import { fetchAccounts } from "../api/trade";

export function NewTaskHook() {
  const [step, setStep] = useState(1);
  const [accounts, setAccounts] = useState([]);

  const [selectedAccount, setSelectedAccount] = useState(null);

  function getAccounts() {
    fetchAccounts().then((data) => {
      const cryptoAccounts = data.crypto_accounts;
      const forexAccounts = data.forex_accounts;
      console.log(cryptoAccounts, forexAccounts);
      setAccounts([...cryptoAccounts, ...forexAccounts]);
    });
  }

  useEffect(() => {
    if (step === 1) getAccounts();
  }, [step]);

  function nextStep(s = null) {
    if (!s) {
      if (step >= 3) return;
      setStep((prev) => prev + 1);
    }
    if (s > 3 || s < 1) return;

    setStep(s);
  }

  return {
    step,
    nextStep,
    accounts,
    selectedAccount,
    setSelectedAccount,
  };
}
