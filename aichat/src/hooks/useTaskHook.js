import { useState } from "react";

export function NewTaskHook() {
  const [step, setStep] = useState(1);

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
  };
}
