import React, { Fragment } from "react";
import { NewTaskHook, type AgentConfig } from "../hooks/useTradeHook";
import type { Account } from "../types/user";
import { ArrowRight, Download, Plus } from "lucide-react";

import { Dropdown } from "../ui/DropDown";

import { HOST } from "../constant";

interface NewTradeTaskProps {
  close: () => void;
}

interface Step1Props {
  config: AgentConfig;
  setConfig: React.Dispatch<React.SetStateAction<AgentConfig>>;
  accounts: Account[];
}

interface Step2Props {
  config: AgentConfig;
  setConfig: React.Dispatch<React.SetStateAction<AgentConfig>>;
}

interface Step3Props {
  config: AgentConfig;
  setConfig: React.Dispatch<React.SetStateAction<AgentConfig>>;
}

function NewTradeTask({ close }: NewTradeTaskProps) {
  const {
    step,
    nextStep,
    accounts,
    config,
    setConfig,
    canContinue,
    stepError,
  } = NewTaskHook();

  return (
    <section className="overflow-y-auto h-full max-h-full w-full  no-scrollbar">
      <div className="pt-4 flex sm:flex-row flex-col-reverse gap-4 justify-between items-end sticky w-full top-0 z-50 ">
        <div className="grid grid-cols-3 rounded-md w-fit gap-4">
          <button
            className={
              step === 1 ? "btn-title  border-none" : "btn-text border-none"
            }
            onClick={() => nextStep(1)}
          >
            <span className="bg-text/20 text-current rounded-full mr-2 h-6 aspect-square flex items-center justify-center text-sm">
              1
            </span>
            Basics
          </button>
          <button
            className={
              step === 2 ? "btn-title  border-none" : "btn-text border-none"
            }
            onClick={() => nextStep(2)}
          >
            <span className="bg-text/20 text-current rounded-full mr-2 h-6 aspect-square flex items-center justify-center text-sm">
              2
            </span>
            Setup
          </button>
          <button
            className={
              step === 3 ? "btn-title  border-none" : "btn-text border-none"
            }
            onClick={() => nextStep(3)}
          >
            <span className="bg-text/20 text-current rounded-full mr-2 h-6 aspect-square flex items-center justify-center text-sm">
              3
            </span>
            Finalize
          </button>
        </div>
        <div className="flex items-center gap-4">
          <button className="btn-icon " onClick={close}>
            Cancel
          </button>
          <button
            className="btn-accent disabled:opacity-50"
            disabled={!canContinue}
            onClick={() => nextStep()}
          >
            {step === 3 ? (
              <Fragment>
                Save
                <Download className="h-4 aspect-auto" />
              </Fragment>
            ) : (
              <Fragment>
                Next
                <ArrowRight className="h-4 aspect-auto" />
              </Fragment>
            )}
          </button>
        </div>
      </div>

      {stepError && (
        <p className="text-xs text-error mt-3 bg-red-950/40 border border-error/60 rounded-md px-3 py-2 max-w-3xl mx-auto">
          {stepError}
        </p>
      )}

      <section className="mt-8 bg-transparent">
        {step === 1 ? (
          <Step1 config={config} setConfig={setConfig} accounts={accounts} />
        ) : step === 2 ? (
          <Step2 config={config} setConfig={setConfig} />
        ) : step === 3 ? (
          <Step3 config={config} setConfig={setConfig} />
        ) : (
          <Fragment></Fragment>
        )}
      </section>
    </section>
  );
}

export default NewTradeTask;

function Step1({ config, setConfig, accounts }: Step1Props) {
  return (
    <div className="space-y-4 max-w-2xl rounded-md p-4 bg-text/5 backdrop-blur-3xl mx-auto">
      <div className="">
        <label className="input-label">Name</label>
        <input
          className="input-text w-full"
          placeholder="My first agent"
          value={config.name}
          onChange={(e) =>
            setConfig((prev) => ({ ...prev, name: e.target.value }))
          }
        />
      </div>

      <div className="">
        <div className="flex items-center justify-between">
          <label className="input-label">Account</label>
          <a href={HOST + "/automate/"} className="btn-icon">
            <Plus className="h-4 aspect-auto" />
          </a>
        </div>
        <Dropdown
          className="w-full"
          btnClassName="input-text cursor-pointer w-full"
          defaultLabel={
            config.selectedAccount
              ? `${config.selectedAccount.name} (${config.selectedAccount.broker_type})`
              : "Select an account"
          }
          options={accounts.map((v) => {
            return {
              label: `${v.name} (${v.broker_type})`,
              onClick: () =>
                setConfig((prev) => ({ ...prev, selectedAccount: v })),
            };
          })}
        />
      </div>
      <div className="">
        <label className="input-label">Instruction</label>
        <textarea
          className="input-text w-full min-h-[200px] no-scrollbar"
          placeholder="Give the agent the overall workflow and behavior."
          value={config.instruction}
          onChange={(e) =>
            setConfig((prev) => ({ ...prev, instruction: e.target.value }))
          }
        />
        <p className="text-xs text-text/60 mt-2">
          Keep this at workflow level: account checks, risk behavior, execution
          discipline, and profitability objective.
        </p>
      </div>
    </div>
  );
}

function Step2({ config, setConfig }: Step2Props) {
  const [newSymbol, setNewSymbol] = React.useState("");
  const handleAddSymbol = () => {
    const symbol = newSymbol.trim().toUpperCase();
    if (symbol && !config.symbols.includes(symbol)) {
      setConfig((prev) => ({ ...prev, symbols: [...prev.symbols, symbol] }));
      setNewSymbol("");
    }
  };
  const handleRemoveSymbol = (symbol: string) => {
    setConfig((prev) => ({
      ...prev,
      symbols: prev.symbols.filter((s) => s !== symbol),
    }));
  };
  return (
    <div className="space-y-6 max-w-2xl rounded-md p-4 bg-text/5 backdrop-blur-3xl mx-auto">
      {/* ── Market ── */}
      <div className="space-y-4">
        <p className="text-xs font-semibold uppercase tracking-wider text-text/50">
          Market
        </p>

        <div>
          <label className="input-label">Symbols</label>
          <div className="flex flex-wrap gap-2 mb-2">
            {config.symbols.map((symbol) => (
              <span
                key={symbol}
                className="inline-flex items-center bg-accent/10 border border-accent/40 rounded px-2 py-1 text-xs text-text"
              >
                {symbol}
                <button
                  type="button"
                  className="ml-1 text-accent hover:text-red-500"
                  onClick={() => handleRemoveSymbol(symbol)}
                  title="Remove"
                >
                  ×
                </button>
              </span>
            ))}
          </div>
          <div className="flex gap-2 items-center">
            <input
              className="input-text w-full"
              placeholder="Add symbol (e.g. BTCUSD)"
              value={newSymbol}
              onChange={(e) => setNewSymbol(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") {
                  e.preventDefault();
                  handleAddSymbol();
                }
              }}
            />
            <button
              type="button"
              className="btn-icon"
              onClick={handleAddSymbol}
              title="Add symbol"
            >
              <Plus className="h-4 aspect-auto" />
            </button>
          </div>
        </div>

        <input
          className="input-text w-full"
          placeholder="Timeframes (comma separated, e.g. 1m,5m,1h)"
          value={config.timeframes || ""}
          onChange={(e) =>
            setConfig((prev) => ({ ...prev, timeframes: e.target.value }))
          }
        />
      </div>

      <div className="border-t border-text/10" />

      {/* ── Risk ── */}
      <div className="space-y-4">
        <p className="text-xs font-semibold uppercase tracking-wider text-text/50">
          Risk
        </p>

        <div>
          <label className="input-label">Position sizing mode</label>
          <div className="flex gap-2 mb-3">
            <button
              type="button"
              className={`btn-text px-3 py-1 rounded ${config.positionSizingMode === "fixed" ? "border-accent" : "border-text/20"}`}
              onClick={() =>
                setConfig((prev) => ({ ...prev, positionSizingMode: "fixed" }))
              }
            >
              Fixed size
            </button>
            <button
              type="button"
              className={`btn-text px-3 py-1 rounded ${config.positionSizingMode === "percentage" ? "border-accent" : "border-text/20"}`}
              onClick={() =>
                setConfig((prev) => ({
                  ...prev,
                  positionSizingMode: "percentage",
                }))
              }
            >
              Percentage risk
            </button>
          </div>
          {config.positionSizingMode === "fixed" ? (
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <NumberInput
                label="Fixed position size (USD)"
                value={config.fixedPositionSizeUsd || ""}
                onChange={(value) =>
                  setConfig((prev) => ({
                    ...prev,
                    fixedPositionSizeUsd: value,
                  }))
                }
              />
            </div>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <NumberInput
                label="% risk per trade"
                value={config.percentRiskPerTrade || ""}
                onChange={(value) =>
                  setConfig((prev) => ({ ...prev, percentRiskPerTrade: value }))
                }
              />
              <NumberInput
                label="Min position size (USD)"
                value={config.minPositionSizeUsd || ""}
                onChange={(value) =>
                  setConfig((prev) => ({ ...prev, minPositionSizeUsd: value }))
                }
              />
              <NumberInput
                label="Max position size (USD)"
                value={config.maxPositionSizeUsd || ""}
                onChange={(value) =>
                  setConfig((prev) => ({ ...prev, maxPositionSizeUsd: value }))
                }
              />
            </div>
          )}
        </div>
      </div>

      <div className="border-t border-text/10" />

      {/* ── Loss limits ── */}
      <div className="space-y-3">
        <SectionToggle
          label="Loss limits"
          enabled={config.lossLimitEnabled}
          onToggle={() =>
            setConfig((prev) => ({
              ...prev,
              lossLimitEnabled: !prev.lossLimitEnabled,
            }))
          }
        />
        {config.lossLimitEnabled && (
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <NumberInput
              label="Max loss / day (USD)"
              value={config.maxDailyLossUsd || ""}
              placeholder="e.g. 100"
              onChange={(value) =>
                setConfig((prev) => ({ ...prev, maxDailyLossUsd: value }))
              }
            />
            <NumberInput
              label="Max loss / trade (USD)"
              value={config.maxLossPerTradeUsd || ""}
              placeholder="e.g. 50"
              onChange={(value) =>
                setConfig((prev) => ({ ...prev, maxLossPerTradeUsd: value }))
              }
            />
            <NumberInput
              label="Max overall loss (USD)"
              value={config.maxOverallLossUsd || ""}
              placeholder="e.g. 500"
              onChange={(value) =>
                setConfig((prev) => ({ ...prev, maxOverallLossUsd: value }))
              }
            />
          </div>
        )}
      </div>

      <div className="border-t border-text/10" />

      {/* ── Profit limits ── */}
      <div className="space-y-3">
        <SectionToggle
          label="Profit limits"
          enabled={config.profitLimitEnabled}
          onToggle={() =>
            setConfig((prev) => ({
              ...prev,
              profitLimitEnabled: !prev.profitLimitEnabled,
            }))
          }
        />
        {config.profitLimitEnabled && (
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <NumberInput
              label="Max profit / day (USD)"
              value={config.maxDailyProfitUsd || ""}
              placeholder="e.g. 200"
              onChange={(value) =>
                setConfig((prev) => ({ ...prev, maxDailyProfitUsd: value }))
              }
            />
            <NumberInput
              label="Max profit / trade (USD)"
              value={config.maxProfitPerTradeUsd || ""}
              placeholder="e.g. 100"
              onChange={(value) =>
                setConfig((prev) => ({ ...prev, maxProfitPerTradeUsd: value }))
              }
            />
            <NumberInput
              label="Max overall profit (USD)"
              value={config.maxOverallProfitUsd || ""}
              placeholder="e.g. 1000"
              onChange={(value) =>
                setConfig((prev) => ({ ...prev, maxOverallProfitUsd: value }))
              }
            />
          </div>
        )}
      </div>

      <div className="border-t border-text/10" />

      {/* ── Trade limits ── */}
      <div className="space-y-3">
        <SectionToggle
          label="Trade limits"
          enabled={config.tradeLimitEnabled}
          onToggle={() =>
            setConfig((prev) => ({
              ...prev,
              tradeLimitEnabled: !prev.tradeLimitEnabled,
            }))
          }
        />
        {config.tradeLimitEnabled && (
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <NumberInput
              label="Max concurrent trades"
              value={config.maxConcurrentTrades || ""}
              placeholder="e.g. 3"
              onChange={(value) =>
                setConfig((prev) => ({ ...prev, maxConcurrentTrades: value }))
              }
            />
            <NumberInput
              label="Max trades / day"
              value={config.maxTradesPerDay || ""}
              placeholder="e.g. 10"
              onChange={(value) =>
                setConfig((prev) => ({ ...prev, maxTradesPerDay: value }))
              }
            />
          </div>
        )}
      </div>

      <div className="border-t border-text/10" />

      {/* ── Setup notes ── */}
      <div>
        <label className="input-label">Trading setup notes</label>
        <textarea
          className="input-text w-full min-h-[80px]"
          placeholder="Describe your preferred trading setup, e.g. trend, breakout, mean reversion, etc. (optional)"
          value={config.tradingSetup || ""}
          onChange={(e) =>
            setConfig((prev) => ({ ...prev, tradingSetup: e.target.value }))
          }
        />
      </div>
    </div>
  );
}

function Step3({ config, setConfig }: Step3Props) {
  return (
    <div className="space-y-4 max-w-2xl rounded-md p-4 bg-text/5 backdrop-blur-3xl mx-auto">
      <div>
        <label className="input-label">Execution mode</label>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
          <ModeCard
            title="Advisory"
            active={config.executionMode === "advisory"}
            description="Suggest ideas only, no orders."
            onClick={() =>
              setConfig((prev) => ({ ...prev, executionMode: "advisory" }))
            }
          />
          <ModeCard
            title="Confirm"
            active={config.executionMode === "confirm"}
            description="Ask for your confirmation before placing orders."
            onClick={() =>
              setConfig((prev) => ({ ...prev, executionMode: "confirm" }))
            }
          />
          <ModeCard
            title="Auto"
            active={config.executionMode === "auto"}
            description="Place orders automatically inside configured risk limits."
            onClick={() =>
              setConfig((prev) => ({ ...prev, executionMode: "auto" }))
            }
          />
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div>
          <label className="input-label">Run frequency</label>
          <input
            className="input-text w-full"
            placeholder="e.g. every 1 min, 10 min, 1h"
            value={config.runFrequency || ""}
            onChange={(e) =>
              setConfig((prev) => ({ ...prev, runFrequency: e.target.value }))
            }
          />
        </div>
        <div>
          <label className="input-label">Agent price (USD/month)</label>
          <input
            type="number"
            min={0}
            className="input-text w-full"
            placeholder="e.g. 10"
            value={config.agentPrice || ""}
            onChange={(e) =>
              setConfig((prev) => ({ ...prev, agentPrice: e.target.value }))
            }
          />
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div>
          <label className="input-label">Active hours (UTC)</label>
          <input
            className="input-text w-full"
            value={config.activeHoursUtc}
            onChange={(e) =>
              setConfig((prev) => ({ ...prev, activeHoursUtc: e.target.value }))
            }
            placeholder="00:00-23:59"
          />
        </div>
        <div>
          <label className="input-label">Cooldown (minutes)</label>
          <input
            type="number"
            min={0}
            className="input-text w-full"
            value={config.cooldownMinutes}
            onChange={(e) =>
              setConfig((prev) => ({
                ...prev,
                cooldownMinutes: e.target.value,
              }))
            }
          />
        </div>
      </div>

      <label className="flex items-center gap-2 text-sm text-text/80">
        <input
          type="checkbox"
          checked={config.requireNewsFilter}
          onChange={(e) =>
            setConfig((prev) => ({
              ...prev,
              requireNewsFilter: e.target.checked,
            }))
          }
        />
        Pause entries around high-impact news events
      </label>

      <div className="rounded-md border border-text/20 p-4 bg-background/30 text-sm space-y-2">
        <p className="btn-title">Review</p>
        <p>
          <span className="text-text/60">Name:</span> {config.name || "-"}
        </p>
        <p>
          <span className="text-text/60">Account:</span>{" "}
          {config.selectedAccount
            ? `${config.selectedAccount.name} (${config.selectedAccount.broker_type})`
            : "-"}
        </p>
        <p>
          <span className="text-text/60">Instruction:</span>{" "}
          {config.instruction ? "Configured" : "Missing"}
        </p>
        <p>
          <span className="text-text/60">Symbols:</span>{" "}
          {config.symbols.join(", ") || "-"}
        </p>
        <p>
          <span className="text-text/60">Timeframes:</span>{" "}
          {config.timeframes || "-"}
        </p>
        <p>
          <span className="text-text/60">Risk:</span>{" "}
          {config.positionSizingMode === "fixed"
            ? `Fixed $${config.fixedPositionSizeUsd || "-"} per trade`
            : `${config.percentRiskPerTrade || "-"}% risk/trade (min $${config.minPositionSizeUsd || "-"}, max $${config.maxPositionSizeUsd || "-"})`}
        </p>
        {config.lossLimitEnabled && (
          <p>
            <span className="text-text/60">Loss limits:</span>{" "}
            {`Day $${config.maxDailyLossUsd || "-"} | Trade $${config.maxLossPerTradeUsd || "-"} | Overall $${config.maxOverallLossUsd || "-"}`}
          </p>
        )}
        {config.profitLimitEnabled && (
          <p>
            <span className="text-text/60">Profit limits:</span>{" "}
            {`Day $${config.maxDailyProfitUsd || "-"} | Trade $${config.maxProfitPerTradeUsd || "-"} | Overall $${config.maxOverallProfitUsd || "-"}`}
          </p>
        )}
        {config.tradeLimitEnabled && (
          <p>
            <span className="text-text/60">Trade limits:</span>{" "}
            {`Concurrent ${config.maxConcurrentTrades || "-"} | Per day ${config.maxTradesPerDay || "-"}`}
          </p>
        )}
        <p>
          <span className="text-text/60">Trading setup:</span>{" "}
          {config.tradingSetup || "-"}
        </p>
        <p>
          <span className="text-text/60">Run frequency:</span>{" "}
          {config.runFrequency || "-"}
        </p>
        <p>
          <span className="text-text/60">Agent price:</span>{" "}
          {config.agentPrice ? `$${config.agentPrice}/month` : "-"}
        </p>
        <p>
          <span className="text-text/60">Active hours:</span>{" "}
          {config.activeHoursUtc}
        </p>
        <p>
          <span className="text-text/60">Cooldown:</span>{" "}
          {config.cooldownMinutes} min
        </p>
        <p>
          <span className="text-text/60">News filter:</span>{" "}
          {config.requireNewsFilter ? "Yes" : "No"}
        </p>
      </div>
    </div>
  );
}

function SectionToggle({
  label,
  enabled,
  onToggle,
}: {
  label: string;
  enabled: boolean;
  onToggle: () => void;
}) {
  return (
    <div className="flex items-center justify-between">
      <span className="text-xs font-semibold uppercase tracking-wider text-text/50">
        {label}
      </span>
      <button
        type="button"
        onClick={onToggle}
        className={`relative inline-flex h-4.5 w-12 items-center rounded-full transition-colors ${
          enabled ? "bg-title" : "bg-text/20"
        }`}
      >
        <span
          className={`inline-block h-3 w-5 transform rounded-full bg-background transition-transform ${
            enabled ? "translate-x-6" : "translate-x-1"
          }`}
        />
      </button>
    </div>
  );
}

function NumberInput({
  label,
  value,
  onChange,
  placeholder,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
}) {
  return (
    <div>
      <label className="input-label">{label}</label>
      <input
        type="number"
        min={0}
        step="0.01"
        className="input-text w-full"
        value={value}
        placeholder={placeholder}
        onChange={(e) => onChange(e.target.value)}
      />
    </div>
  );
}

function ModeCard({
  title,
  description,
  active,
  onClick,
}: {
  title: string;
  description: string;
  active: boolean;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`rounded-md border p-3 text-left ${
        active
          ? "border-accent bg-accent/10"
          : "border-text/20 bg-background/20"
      }`}
    >
      <p className="btn-title">{title}</p>
      <p className="text-xs text-text/70 mt-1">{description}</p>
    </button>
  );
}
