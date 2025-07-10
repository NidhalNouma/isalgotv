import React, { Fragment } from "react";
import { NewTaskHook } from "../hooks/useTaskHook";
import { ArrowRight, Download } from "lucide-react";

function NewTradeTask({ close }) {
  const { step, nextStep } = NewTaskHook();
  return (
    <section className="overflow-y-scroll h-screen max-h-screen">
      <div className="pt-4 flex sm:flex-row flex-col-reverse gap-4 justify-between items-end sticky top-0 z-10 nav-bg via-80%">
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

      <section className="mt-8">
        {step === 1 ? (
          <Step1 nextFn={() => nextStep(2)} />
        ) : (
          <Fragment></Fragment>
        )}
      </section>
    </section>
  );
}

export default NewTradeTask;

function Step1({ nextFn }) {
  return (
    <div className="space-y-4 max-w-md roubded-md p-4 bg-text/5 backdrop-blur-3xl mx-auto">
      <div className="">
        <label className="input-label">Name</label>
        <input className="input-text w-full" />
      </div>
      <div className="">
        <label className="input-label">Description</label>
        <input className="input-text w-full" />
      </div>
      <div className="">
        <label className="input-label">Instraction</label>
        <textarea className="input-text w-full" />
      </div>
      <div className="">
        <label className="input-label">Account</label>
        <select className="input-text w-full" />
      </div>
    </div>
  );
}
