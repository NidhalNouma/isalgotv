import { Fragment } from "react";
import { X } from "lucide-react";

export function AuthPopup({ onClose }) {
  return (
    <Fragment>
      <div className="fixed inset-0 bg-background/60 z-40" onClick={onClose} />
      <div className="fixed left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 w-full max-w-md z-50 p-8">
        <div className="bg-text/10 backdrop-blur-3xl rounded-md shadow-xl p-6">
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-xl font-semibold text-text">
              Continue with SARO
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
              href="/my/register"
              className="w-full btn-primary transition-colors"
            >
              Sign up
            </a>

            <a
              href="/my/login"
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

export function UpgradePopup({ onClose }) {
  return (
    <Fragment>
      <div className="fixed inset-0 bg-background/60 z-40" onClick={onClose} />
      <div className="fixed left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 w-full max-w-md z-50 p-8">
        <div className="bg-text/10 backdrop-blur-3xl rounded-md shadow-xl p-6">
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
              href="/my/membership/"
              className="w-full btn-primary transition-colors"
            >
              Upgrade
            </a>
          </div>
        </div>
      </div>
    </Fragment>
  );
}
