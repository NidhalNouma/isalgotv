import { Fragment, useState, useEffect } from "react";
import { Paperclip, Square } from "lucide-react";
import { AuthPopup } from "./ui/Popup";
import { SendMessageHook } from "../hooks/useChatHook";

import { Dropdown } from "./ui/DropDown";

export default function ChatInput({
  onSend,
  disable = false,
  className = "",
  quickActionMsg,
  focus = false,
}) {
  const [showAuthPopup, setShowAuthPopup] = useState(false);

  const {
    input,
    setInput,
    files,
    fileInputRef,
    textareaRef,
    setFiles,
    handleSubmit,
    handleFileChange,
    handleKeyDown,
    handleInput,

    models,
    model,
    setModel,
  } = SendMessageHook(onSend, () => setShowAuthPopup(true));

  const containerClass = className
    ? className + " mb-4 z-20"
    : "mt-auto w-full bg-transparent sticky left-0 right-0 bottom-0 pb-2 z-20";

  useEffect(() => {
    if (quickActionMsg) {
      if (input !== quickActionMsg) setInput(quickActionMsg);
      else if (input === quickActionMsg) handleSubmit();
    }
  }, [quickActionMsg, input]);

  return (
    <Fragment>
      {showAuthPopup && <AuthPopup onClose={() => setShowAuthPopup(false)} />}

      <div className={containerClass}>
        <form
          onSubmit={handleSubmit}
          className="max-w-3xl mx-auto pb-2 py-4 md:px-2 px-0"
        >
          <div className="relative rounded-3xl bg-text/10">
            {files.length > 0 && (
              <div className="px-4 pt-2">
                <div className="flex flex-wrap gap-2">
                  {files.map((file, index) => (
                    <div
                      key={index}
                      className="bg-text/10 px-2 py-1 rounded text-sm flex items-center gap-1 "
                    >
                      <span className="truncate max-w-[200px] text-text/60">
                        {file.name}
                      </span>
                      <button
                        type="button"
                        onClick={() =>
                          setFiles(files.filter((_, i) => i !== index))
                        }
                        className="text-text/40 hover:text-text/60"
                      >
                        ×
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            )}
            <div className="flex flex-col items-start">
              <textarea
                name="message"
                autoFocus={focus}
                ref={textareaRef}
                value={input}
                onChange={handleInput}
                onKeyDown={handleKeyDown}
                placeholder="Ask Saro"
                rows={1}
                className="w-full text-text placeholder:text-text/40 px-4 pt-4 pb-2 bg-transparent border-none border-0 rounded-xl focus:outline-none focus:ring-0 disabled:opacity-50 resize-none min-h-[56px] max-h-[200px] overflow-y-auto scrollbar-hide"
                style={{ height: "auto", resize: "none" }}
              />
              <div className="flex items-center w-full px-2 pb-1">
                <button
                  type="button"
                  onClick={() => fileInputRef.current?.click()}
                  className="p-2 text-text/60 hover:text-text/70 disabled:opacity-50"
                >
                  <Paperclip className="w-5 aspect-auto" />
                </button>
                <Dropdown
                  defaultLabel={model.name}
                  className="btn-text rounded-3xl text-xs py-0 px-2.5 opacity-80 "
                  options={
                    models.map((m) => ({
                      label: m.name,
                      description: m.description,
                      onClick: () => setModel(m),
                    })) || []
                  }
                ></Dropdown>
                <div className="!ml-auto"></div>
                <input
                  type="file"
                  ref={fileInputRef}
                  onChange={handleFileChange}
                  multiple
                  className="hidden"
                />
                {disable ? (
                  <button
                    type="button"
                    className="p-2 text-background hover:text-background disabled:opacity-50"
                  >
                    <Square className=" p-1.5 w-6 aspect-auto fill-background bg-text/80 hover:bg-text rounded-full" />
                  </button>
                ) : (
                  <button
                    type="submit"
                    disabled={disable}
                    className="p-2 text-background hover:text-background disabled:opacity-50"
                  >
                    {/* <SendHorizontal className="w-5 h-5" /> */}
                    <svg
                      className="w-6 h-6 bg-text/80 hover:bg-text rounded-full"
                      viewBox="0 0 32 32"
                      fill="none"
                      xmlns="http://www.w3.org/2000/svg"
                    >
                      <path
                        fillRule="evenodd"
                        clipRule="evenodd"
                        d="M15.1918 8.90615C15.6381 8.45983 16.3618 8.45983 16.8081 8.90615L21.9509 14.049C22.3972 14.4953 22.3972 15.2189 21.9509 15.6652C21.5046 16.1116 20.781 16.1116 20.3347 15.6652L17.1428 12.4734V22.2857C17.1428 22.9169 16.6311 23.4286 15.9999 23.4286C15.3688 23.4286 14.8571 22.9169 14.8571 22.2857V12.4734L11.6652 15.6652C11.2189 16.1116 10.4953 16.1116 10.049 15.6652C9.60265 15.2189 9.60265 14.4953 10.049 14.049L15.1918 8.90615Z"
                        fill="currentColor"
                      ></path>
                    </svg>
                  </button>
                )}
              </div>
            </div>
          </div>
          {/* <p className="text-xs text-center text-text/50 mt-2 mb-0">
            IsalGo AI can make mistakes. Consider checking important information.
          </p> */}
        </form>
      </div>
    </Fragment>
  );
}
