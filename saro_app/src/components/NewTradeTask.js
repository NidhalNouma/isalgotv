import React, { Fragment } from "react";
import { NewTaskHook } from "../hooks/useTaskHook";
import { ArrowRight, Download, Plus } from "lucide-react";

import { Dropdown } from "../components/ui/DropDown";

import { HOST } from "../constant";

function NewTradeTask({ close }) {
  const { step, nextStep, accounts, selectedAccount, setSelectedAccount } =
    NewTaskHook();

  return (
    <section className="overflow-y-auto h-full max-h-full w-full">
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
            Configure
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
            Start
          </button>
        </div>
        <div className="flex items-center gap-4">
          <button className="btn-icon " onClick={close}>
            Cancel
          </button>
          <button className="btn-accent " onClick={() => nextStep()}>
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

      <section className="mt-8 bg-transparent">
        {step === 1 ? (
          <Step1
            nextFn={() => nextStep(2)}
            accounts={accounts}
            selectedAccount={selectedAccount}
            setSelectedAccount={setSelectedAccount}
          />
        ) : (
          <Fragment></Fragment>
        )}
      </section>
    </section>
  );
}

export default NewTradeTask;

function Step1({ nextFn, accounts, selectedAccount, setSelectedAccount }) {
  return (
    <div className="space-y-4 max-w-md rounded-md p-4 bg-text/5 backdrop-blur-3xl mx-auto">
      <div className="">
        <label className="input-label">Name</label>
        <input className="input-text w-full" placeholder="My first agent" />
      </div>
      {/* <div className="">
        <label className="input-label">Description</label>
        <input className="input-text w-full" />
      </div>
      <div className="">
        <label className="input-label">Instraction</label>
        <textarea className="input-text w-full" />
      </div> */}
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
          options={accounts.map((v) => {
            return {
              label: `${v.name} (${v.broker_type})`,
              onClick: (e) => setSelectedAccount(`${v.id}#${v.broker_type}`),
            };
          })}
        />
        {/* <select
          className="input-text w-full cursor-pointer"
          value={selectedAccount}
          onChange={(e) => setSelectedAccount(e.target.value)}
        >
          <option value="" disabled selected hidden>
            Select an account
          </option>
          {accounts.map((acc, i) => (
            <option
              key={i}
              value={`${acc.id}#${acc.broker_type}`}
              selected={selectedAccount === `${acc.id}#${acc.broker_type}`}
              disabled={!acc.active}
            >
              {acc.name} ({acc.broker_type})
            </option>
          ))}
        </select> */}
      </div>
    </div>
  );
}
