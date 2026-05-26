import { useState, useEffect } from "react";
import { useUser } from "../contexts/UserContext";

import type { Account } from "../types/user";

export type AgentExecutionMode = "advisory" | "confirm" | "auto";

export const DEFAULT_AGENT_INSTRUCTION = `You are a cautious but opportunity-seeking trading agent.

Primary goal:
- Be consistently profitable over time while protecting capital first.

Required workflow for every cycle:
1) Check the selected broker account status and balances.
2) Check open positions/orders and decide if anything must be adjusted.
3) Evaluate market structure and momentum before any action.
4) If setup quality is low or risk is unclear, do not trade.
5) If setup quality is acceptable, follow risk limits strictly.
6) Re-check exposure after execution and keep risk controlled.

Rules:
- Prefer no trade over low-confidence trade.
- Respect max daily loss and max concurrent trades at all times.
- Reduce risk after losses and avoid revenge trading.
- Explain the reasoning for each important decision.`;

export type PositionSizingMode = "fixed" | "percentage";

export interface AgentConfig {
  name: string;
  instruction: string;
  selectedAccount: Account | null;
  // Step 2 additions
  symbols: string[];
  timeframes?: string;
  // Position sizing
  positionSizingMode: PositionSizingMode;
  fixedPositionSizeUsd?: string;
  percentRiskPerTrade?: string;
  minPositionSizeUsd?: string;
  maxPositionSizeUsd?: string;
  tradingSetup?: string;
  // Loss limits (toggleable)
  lossLimitEnabled: boolean;
  maxDailyLossUsd?: string;
  maxLossPerTradeUsd?: string;
  maxOverallLossUsd?: string;
  // Profit limits (toggleable)
  profitLimitEnabled: boolean;
  maxDailyProfitUsd?: string;
  maxProfitPerTradeUsd?: string;
  maxOverallProfitUsd?: string;
  // Trade limits (toggleable)
  tradeLimitEnabled: boolean;
  maxConcurrentTrades?: string;
  maxTradesPerDay?: string;
  // Step 3 additions
  runFrequency?: string;
  agentPrice?: string;
  executionMode: AgentExecutionMode;
  activeHoursUtc: string;
  cooldownMinutes: string;
  requireNewsFilter: boolean;
}

interface NewTaskState {
  step: number;
  nextStep: (s?: number | null) => void;
  accounts: Account[];
  config: AgentConfig;
  setConfig: React.Dispatch<React.SetStateAction<AgentConfig>>;
  canContinue: boolean;
  stepError: string | null;
  submitLabel: string;
  saveAgentConfig: () => void;
}

export function NewTaskHook(): NewTaskState {
  const { accounts, getAccounts } = useUser();

  const [step, setStep] = useState<number>(1);
  const [stepError, setStepError] = useState<string | null>(null);
  const [config, setConfig] = useState<AgentConfig>({
    name: "",
    instruction: DEFAULT_AGENT_INSTRUCTION,
    selectedAccount: null,
    symbols: [],
    timeframes: "",
    positionSizingMode: "fixed",
    fixedPositionSizeUsd: "100",
    percentRiskPerTrade: "1",
    minPositionSizeUsd: "",
    maxPositionSizeUsd: "",
    tradingSetup: "",
    lossLimitEnabled: false,
    maxDailyLossUsd: "",
    maxLossPerTradeUsd: "",
    maxOverallLossUsd: "",
    profitLimitEnabled: false,
    maxDailyProfitUsd: "",
    maxProfitPerTradeUsd: "",
    maxOverallProfitUsd: "",
    tradeLimitEnabled: false,
    maxConcurrentTrades: "",
    maxTradesPerDay: "",
    runFrequency: "",
    agentPrice: "",
    executionMode: "confirm",
    activeHoursUtc: "00:00-23:59",
    cooldownMinutes: "5",
    requireNewsFilter: false,
  });

  useEffect(() => {
    if (step === 1) getAccounts();
  }, [step]);

  const step2PositionValid =
    config.positionSizingMode === "fixed"
      ? Number(config.fixedPositionSizeUsd) > 0
      : Number(config.percentRiskPerTrade) > 0;

  const canContinue =
    (step === 1 &&
      config.name.trim().length >= 3 &&
      config.instruction.trim().length >= 30 &&
      config.selectedAccount !== null) ||
    (step === 2 && step2PositionValid) ||
    (step === 3 && config.runFrequency?.trim().length! > 0);

  function validateStep(stepNumber: number): string | null {
    if (stepNumber === 1) {
      if (config.name.trim().length < 3)
        return "Agent name must be at least 3 characters.";
      if (config.instruction.trim().length < 30)
        return "Instruction must be at least 30 characters so the agent can reason clearly.";
      if (!config.selectedAccount) return "Please select a broker account.";
      return null;
    }

    if (stepNumber === 2) {
      if (config.positionSizingMode === "fixed") {
        if (Number(config.fixedPositionSizeUsd) <= 0)
          return "Fixed position size must be greater than 0.";
      } else {
        if (Number(config.percentRiskPerTrade) <= 0)
          return "Percentage risk per trade must be greater than 0.";
      }
      return null;
    }

    if (stepNumber === 3) {
      if (!config.runFrequency?.trim())
        return "Please select how often the agent should run.";
      return null;
    }

    return null;
  }

  function saveAgentConfig() {
    console.log("Agent config ready", config);
  }

  function nextStep(s: number | null = null) {
    setStepError(null);

    if (!s) {
      const error = validateStep(step);
      if (error) {
        setStepError(error);
        return;
      }

      if (step >= 3) {
        saveAgentConfig();
        return;
      }

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
    config,
    setConfig,
    canContinue,
    stepError,
    submitLabel: step === 3 ? "Save" : "Next",
    saveAgentConfig,
  };
}
