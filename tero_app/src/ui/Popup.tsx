import { Fragment, useEffect, useState, type ReactNode } from "react";
import { X, ExternalLink } from "lucide-react";

import { type User, type Tokens } from "../contexts/UserContext";

import { HOST } from "../constant";

// Ensure TypeScript knows about the global helper
declare global {
  interface Window {
    buyAiToken?: () => void;
  }
}

type CloseHandler = () => void;

type AuthPopupProps = {
  onClose: CloseHandler;
};

export function AuthPopup({ onClose }: AuthPopupProps) {
  return (
    <Fragment>
      <div className="fixed inset-0 backdrop-color z-40" onClick={onClose} />
      <div className="fixed left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 w-full max-w-md z-50 p-8">
        <div className="bg-background/60 dark:bg-text/10 backdrop-blur-3xl rounded-md shadow-xl p-6">
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-xl font-semibold text-text">
              Continue with TERO
            </h2>
            <button onClick={onClose} className="btn-icon transition-colors">
              <X className="w-5 h-5" />
            </button>
          </div>

          <p className="text-text/80 mb-8">
            Sign up to save your chat history and continue the conversation
            across devices.
          </p>

          <div className="space-y-4">
            <a
              href={HOST + "/my/register"}
              className="w-full btn-accent transition-colors"
            >
              Sign up
            </a>

            <a
              href={HOST + "/my/login"}
              className="w-full btn-text from-transparent to-transparent py-2 text-text border border-text/60 transition-colors"
            >
              Sign in
            </a>

            <p className="text-xs text-center text-text/30">
              By continuing, you agree to our Terms of Service and Privacy
              Policy.
            </p>
          </div>
        </div>
      </div>
    </Fragment>
  );
}

type UpgradePopupProps = {
  onClose: CloseHandler;
};

export function UpgradePopup({ onClose }: UpgradePopupProps) {
  return (
    <Fragment>
      <div className="fixed inset-0 backdrop-color z-40" onClick={onClose} />
      <div className="fixed left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 w-full max-w-md z-50 p-8">
        <div className="bg-background/60 dark:bg-text/10 backdrop-blur-3xl rounded-md shadow-xl p-6">
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-xl font-semibold text-text">Upgrade</h2>
            <button onClick={onClose} className="btn-icon transition-colors">
              <X className="w-5 h-5" />
            </button>
          </div>

          <p className="text-text/80 mb-8">
            This feature is only availble for lifetime members consider
            upgrading to get access.
          </p>

          <div className="space-y-4">
            <a
              href={HOST + "/my/membership/"}
              className="w-full btn-accent transition-colors"
            >
              Upgrade
            </a>
          </div>
        </div>
      </div>
    </Fragment>
  );
}

type DeleteConfirmPopupProps = {
  children: ReactNode;
  title: string;
  onClose: CloseHandler;
  onDelete: () => void;
};

export function DeleteConfirmPopup({
  children,
  title,
  onClose,
  onDelete,
}: DeleteConfirmPopupProps) {
  return (
    <Fragment>
      <div className="fixed inset-0 backdrop-color z-40" onClick={onClose} />
      <div className="fixed left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 w-full max-w-md z-50 p-8">
        <div className="bg-background/60 dark:bg-text/10 backdrop-blur-3xl rounded-md shadow-xl p-6">
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-xl font-semibold text-text">{title}</h2>
            <button onClick={onClose} className="btn-icon transition-colors">
              <X className="w-5 h-5" />
            </button>
          </div>

          <p className="text-text/80 mb-8">{children}</p>

          <div className="flex items-center gap-3 justify-center">
            <button
              onClick={onClose}
              className="w-full btn-text transition-colors"
            >
              Cancel
            </button>
            <button
              onClick={onDelete}
              className="w-full btn-primary bg-error transition-colors"
            >
              Delete
            </button>
          </div>
        </div>
      </div>
    </Fragment>
  );
}

type TokensPopupProps = {
  onClose: CloseHandler;
  user?: User | null | undefined;
  tokens: Tokens;
};

export function TokensPopup({ onClose, tokens }: TokensPopupProps) {
  return (
    <Fragment>
      <div className="fixed inset-0 backdrop-color z-40" onClick={onClose} />
      <div className="fixed left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 w-full max-w-xl z-50 p-8">
        <div className="bg-background/60 dark:bg-text/10 backdrop-blur-3xl rounded-md shadow-xl p-6">
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-xl font-semibold text-text">Tokens</h2>
            <button onClick={onClose} className="btn-icon transition-colors">
              <X className="w-5 h-5" />
            </button>
          </div>

          <section className="mb-8 space-y-4">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
              <div>
                <label className="input-label flex items-center gap-1.5">
                  <svg
                    className="w-3.5 aspect-auto"
                    xmlns="http://www.w3.org/2000/svg"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  >
                    <path d="M11 15h2a2 2 0 1 0 0-4h-3c-.6 0-1.1.2-1.4.6L3 17"></path>
                    <path d="m7 21 1.6-1.4c.3-.4.8-.6 1.4-.6h4c1.1 0 2.1-.4 2.8-1.2l4.6-4.4a2 2 0 0 0-2.75-2.91l-4.2 3.9"></path>
                    <path d="m2 16 6 6"></path>
                    <circle cx="16" cy="9" r="2.9"></circle>
                    <circle cx="6" cy="5" r="3"></circle>
                  </svg>
                  Free Daily Tokens
                </label>
                <span className="text-text/80 text-sm">{tokens.free}</span>
              </div>
              <div>
                <label className="input-label flex items-center gap-1.5">
                  <svg
                    className="w-3.5 aspect-auto"
                    xmlns="http://www.w3.org/2000/svg"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  >
                    <circle cx="8" cy="8" r="6"></circle>
                    <path d="M18.09 10.37A6 6 0 1 1 10.34 18"></path>
                    <path d="M7 6h1v4"></path>
                    <path d="m16.71 13.88.7.71-2.82 2.82"></path>
                  </svg>
                  Available Tokens
                </label>
                <span className="text-text/80 text-sm">{tokens.availabel}</span>
              </div>
              <div className="sm:col-start-2">
                <button
                  onClick={() => {
                    onClose();
                    window.buyAiToken?.();
                  }}
                  className="w-full btn-text "
                >
                  Buy Tokens
                </button>
              </div>
            </div>
          </section>
        </div>
      </div>
    </Fragment>
  );
}

type SettingsPopupProps = {
  onClose: CloseHandler;
  user?: User | null | undefined;
};

export function SettingsPopup({ onClose, user }: SettingsPopupProps) {
  const [theme, setTheme] = useState<string>(() => {
    return localStorage.getItem("color-theme") || "light";
  });

  useEffect(() => {
    if (theme === "dark") {
      document.documentElement.classList.add("dark");
      localStorage.setItem("color-theme", "dark");
    } else {
      document.documentElement.classList.remove("dark");
      localStorage.setItem("color-theme", "light");
    }
  }, [theme]);

  return (
    <Fragment>
      <div className="fixed inset-0 backdrop-color z-40" onClick={onClose} />
      <div className="fixed left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 w-full max-w-xl z-50 p-8">
        <div className="bg-background/60 dark:bg-text/10 backdrop-blur-3xl rounded-md shadow-xl p-6">
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-xl font-semibold text-text">Settings</h2>
            <button onClick={onClose} className="btn-icon transition-colors">
              <X className="w-5 h-5" />
            </button>
          </div>

          <section className="mb-8 space-y-6">
            <div>
              <label className="input-label flex items-center gap-1.5">
                <svg
                  className="w-3.5 aspect-auto"
                  xmlns="http://www.w3.org/2000/svg"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                >
                  <path d="m15.477 12.89 1.515 8.526a.5.5 0 0 1-.81.47l-3.58-2.687a1 1 0 0 0-1.197 0l-3.586 2.686a.5.5 0 0 1-.81-.469l1.514-8.526"></path>
                  <circle cx="12" cy="8" r="6"></circle>
                </svg>
                Membership
              </label>
              <span className="text-text/80 text-sm">
                {user?.isLifetime ? (
                  <Fragment>
                    You are a lifetime member! Thank you for your support.
                  </Fragment>
                ) : user?.hasSubscription ? (
                  <Fragment>
                    You are a member! Your have a{" "}
                    <span className="text-text font-semibold">
                      {user?.subscriptionPlan}
                    </span>{" "}
                    plan.{" "}
                    <a href={HOST + "/my/membership/"} className="btn-icon  ">
                      Manage here
                      <ExternalLink className="w-3 aspect-auto ml-1" />
                    </a>
                  </Fragment>
                ) : (
                  <Fragment>
                    You are not a member! consider upgrading.
                    <a href={HOST + "/my/membership/"} className="btn-icon  ">
                      Upgrade here
                      <ExternalLink className="w-3 aspect-auto ml-1" />
                    </a>
                  </Fragment>
                )}
              </span>
            </div>
            <div>
              <label className="input-label flex items-center gap-1.5">
                <svg
                  className="w-3.5 aspect-auto"
                  fill="currentColor"
                  viewBox="0 0 20 20"
                  xmlns="http://www.w3.org/2000/svg"
                >
                  <path
                    d="M2.65621 11.2604H17.0833M5.99996 17.7604L14 17.7604M7.66923 14.375V17.7604M12.3307 14.375V17.7604M3.95829 14.375H16.0416C16.9621 14.375 17.7083 13.6288 17.7083 12.7083V4.79167C17.7083 3.87119 16.9621 3.125 16.0416 3.125H3.95829C3.03782 3.125 2.29163 3.87119 2.29163 4.79167V12.7083C2.29163 13.6288 3.03782 14.375 3.95829 14.375Z"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="1.5"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  ></path>
                </svg>
                Theme
              </label>
              <div className="grid grid-cols-3 gap-4 mt-3">
                <label className="inline-flex items-center gap-2 input-label cursor-pointer">
                  <input
                    type="radio"
                    name="theme"
                    value="light"
                    className="input-text rounded-full px-0 py-0"
                    checked={theme === "light"}
                    onChange={() => setTheme("light")}
                  />
                  <span className="text-text/80 text-xs">Light</span>
                </label>
                <label className="inline-flex items-center gap-2 input-label cursor-pointer">
                  <input
                    type="radio"
                    name="theme"
                    value="dark"
                    className="input-text rounded-full px-0 py-0"
                    checked={theme === "dark"}
                    onChange={() => setTheme("dark")}
                  />
                  <span className="text-text/80 text-xs">Dark</span>
                </label>
              </div>
            </div>

            <div>
              <label className="input-label flex items-center gap-1.5">
                <svg
                  className="w-3.5 aspect-auto"
                  xmlns="http://www.w3.org/2000/svg"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                >
                  <path d="M12 2a10 10 0 1 0 10 10A10 10 0 0 0 12 2z"></path>
                  <path d="M12 8v4"></path>
                  <path d="M12 16h.01"></path>
                </svg>
                About
              </label>
              <span className="text-text/80 text-sm">
                TERO is an AI-powered trading assistant that helps you make
                informed trading decisions.
              </span>
            </div>

            <div>
              <label className="input-label flex items-center gap-1.5">
                <svg
                  className="h-3.5 aspect-auto"
                  stroke="currentColor"
                  fill="currentColor"
                  strokeWidth="0"
                  viewBox="0 0 512 512"
                  xmlns="http://www.w3.org/2000/svg"
                >
                  <path
                    fill="none"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth="32"
                    d="M262.29 192.31a64 64 0 1 0 57.4 57.4 64.13 64.13 0 0 0-57.4-57.4zM416.39 256a154.34 154.34 0 0 1-1.53 20.79l45.21 35.46a10.81 10.81 0 0 1 2.45 13.75l-42.77 74a10.81 10.81 0 0 1-13.14 4.59l-44.9-18.08a16.11 16.11 0 0 0-15.17 1.75A164.48 164.48 0 0 1 325 400.8a15.94 15.94 0 0 0-8.82 12.14l-6.73 47.89a11.08 11.08 0 0 1-10.68 9.17h-85.54a11.11 11.11 0 0 1-10.69-8.87l-6.72-47.82a16.07 16.07 0 0 0-9-12.22 155.3 155.3 0 0 1-21.46-12.57 16 16 0 0 0-15.11-1.71l-44.89 18.07a10.81 10.81 0 0 1-13.14-4.58l-42.77-74a10.8 10.8 0 0 1 2.45-13.75l38.21-30a16.05 16.05 0 0 0 6-14.08c-.36-4.17-.58-8.33-.58-12.5s.21-8.27.58-12.35a16 16 0 0 0-6.07-13.94l-38.19-30A10.81 10.81 0 0 1 49.48 186l42.77-74a10.81 10.81 0 0 1 13.14-4.59l44.9 18.08a16.11 16.11 0 0 0 15.17-1.75A164.48 164.48 0 0 1 187 111.2a15.94 15.94 0 0 0 8.82-12.14l6.73-47.89A11.08 11.08 0 0 1 213.23 42h85.54a11.11 11.11 0 0 1 10.69 8.87l6.72 47.82a16.07 16.07 0 0 0 9 12.22 155.3 155.3 0 0 1 21.46 12.57 16 16 0 0 0 15.11 1.71l44.89-18.07a10.81 10.81 0 0 1 13.14 4.58l42.77 74a10.8 10.8 0 0 1-2.45 13.75l-38.21 30a16.05 16.05 0 0 0-6.05 14.08c.33 4.14.55 8.3.55 12.47z"
                  ></path>
                </svg>
                <a
                  href={HOST + "/my/settings"}
                  className="btn-icon ml-0 pl-0 text-sm"
                >
                  More settings
                  <ExternalLink className="w-3 aspect-auto ml-1" />
                </a>
              </label>
            </div>
          </section>
        </div>
      </div>
    </Fragment>
  );
}
