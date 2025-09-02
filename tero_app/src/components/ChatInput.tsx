import React, { Fragment, useState, useEffect, useRef } from "react";
import { Paperclip, Square } from "lucide-react";
import { AuthPopup } from "../ui/Popup";
import { Dropdown } from "../ui/DropDown";

import { useUser } from "../contexts/UserContext";

import { type AIModel } from "../types/user";

interface ChatInputProps {
  className?: string;
  quickActionMsg?: string | null;
  focus?: boolean;

  input: string;
  setInput: React.Dispatch<React.SetStateAction<string>>;
  files: File[];
  setFiles: React.Dispatch<React.SetStateAction<File[]>>;
  onSend: (e?: React.FormEvent<HTMLTextAreaElement>) => Promise<void> | void;

  models: AIModel[] | undefined;
  model: AIModel;
  setModel: React.Dispatch<React.SetStateAction<AIModel>>;

  loading: Boolean;
}

export default function ChatInput({
  className = "",
  quickActionMsg,
  focus = false,

  input,
  setInput,
  files,
  setFiles,
  onSend,

  models,
  model,
  setModel,

  loading,
}: ChatInputProps) {
  const [showAuthPopup, setShowAuthPopup] = useState<Boolean>(false);

  const { user } = useUser();

  const containerClass = className
    ? className + " mb-4 z-20"
    : "mt-auto w-full bg-transparent sticky left-0 right-0 bottom-0 pb-2 z-20";

  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const textareaRef = useRef<HTMLTextAreaElement | null>(null);

  useEffect(() => {
    if (quickActionMsg) {
      if (input !== quickActionMsg) setInput(quickActionMsg);
      else if (input === quickActionMsg) handleSubmit();
    }
  }, [quickActionMsg, input]);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      setFiles(Array.from(e.target.files));
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  const handleInput = (e: React.FormEvent<HTMLTextAreaElement>) => {
    const textarea = e.currentTarget;
    setInput(textarea.value);
    textarea.style.height = "auto";
    textarea.style.height = `${textarea.scrollHeight}px`;
  };

  const handleSubmit = async (e: any | null = null) => {
    e?.preventDefault();

    const msg = input.trim() || "";

    if ((msg || files.length > 0) && !loading) {
      if (!user) {
        setShowAuthPopup(true);
        return;
      }

      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }
      if (textareaRef.current) {
        textareaRef.current.style.height = "auto";
      }

      onSend();
    }
  };

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
                placeholder="Ask Tero"
                rows={1}
                className="w-full text-text placeholder:text-text/40 px-4 pt-4 pb-2 bg-transparent border-none border-0 rounded-xl focus:outline-none focus:ring-0 disabled:opacity-50 resize-none min-h-[56px] max-h-[200px] overflow-y-auto scrollbar-hide"
                style={{ height: "auto", resize: "none" }}
              />
              <div className="flex items-center px-2 gap-3 w-full pb-1">
                <button
                  type="button"
                  onClick={() => fileInputRef.current?.click()}
                  className="ml-2 text-text/60 hover:text-text/70 disabled:opacity-50"
                >
                  <Paperclip className="w-4 aspect-auto" />
                </button>
                {/* <Dropdown
                  defaultLabel={(model as any)?.name ?? String(model)}
                  btnClassName="btn-text rounded-3xl text-xs py-1 px-2.5 opacity-80 "
                  options={
                    Array.isArray(models)
                      ? (models as any[]).map((m) => ({
                          label: (m as any)?.name ?? String(m),
                          description: (m as any)?.description,
                          onClick: () => setModel(m as any),
                        }))
                      : []
                  }
                >
                  <svg
                    viewBox="0 0 20 20"
                    fill="currentColor"
                    xmlns="http://www.w3.org/2000/svg"
                    className="w-4 aspect-auto"
                  >
                    <path d="M7.45996 14.375C7.45996 13.3616 6.63844 12.54 5.625 12.54C4.61156 12.54 3.79004 13.3616 3.79004 14.375C3.79004 15.3884 4.61156 16.21 5.625 16.21C6.63844 16.21 7.45996 15.3884 7.45996 14.375ZM16.21 14.375C16.21 13.3616 15.3884 12.54 14.375 12.54C13.3616 12.54 12.54 13.3616 12.54 14.375C12.54 15.3884 13.3616 16.21 14.375 16.21C15.3884 16.21 16.21 15.3884 16.21 14.375ZM7.45996 5.625C7.45996 4.61156 6.63844 3.79004 5.625 3.79004C4.61156 3.79004 3.79004 4.61156 3.79004 5.625C3.79004 6.63844 4.61156 7.45996 5.625 7.45996C6.63844 7.45996 7.45996 6.63844 7.45996 5.625ZM16.21 5.625C16.21 4.61156 15.3884 3.79004 14.375 3.79004C13.3616 3.79004 12.54 4.61156 12.54 5.625C12.54 6.63844 13.3616 7.45996 14.375 7.45996C15.3884 7.45996 16.21 6.63844 16.21 5.625ZM17.54 14.375C17.54 16.123 16.123 17.54 14.375 17.54C12.627 17.54 11.21 16.123 11.21 14.375C11.21 12.627 12.627 11.21 14.375 11.21C16.123 11.21 17.54 12.627 17.54 14.375ZM8.79004 5.625C8.79004 7.37298 7.37298 8.79004 5.625 8.79004C3.87702 8.79004 2.45996 7.37298 2.45996 5.625C2.45996 3.87702 3.87702 2.45996 5.625 2.45996C7.37298 2.45996 8.79004 3.87702 8.79004 5.625ZM17.54 5.625C17.54 7.37298 16.123 8.79004 14.375 8.79004C13.7416 8.79004 13.153 8.60173 12.6582 8.28125L8.28125 12.6582C8.60173 13.153 8.79004 13.7416 8.79004 14.375C8.79004 16.123 7.37298 17.54 5.625 17.54C3.87702 17.54 2.45996 16.123 2.45996 14.375C2.45996 12.627 3.87702 11.21 5.625 11.21C6.25794 11.21 6.84623 11.3977 7.34082 11.7178L11.7178 7.34082C11.3977 6.84623 11.21 6.25794 11.21 5.625C11.21 3.87702 12.627 2.45996 14.375 2.45996C16.123 2.45996 17.54 3.87702 17.54 5.625Z"></path>
                  </svg>
                </Dropdown> */}
                <Dropdown
                  defaultLabel={(model as any)?.name ?? String(model)}
                  btnClassName="btn-text rounded-3xl text-xs py-0 px-2.5 opacity-80 "
                  options={
                    Array.isArray(models)
                      ? (models as any[]).map((m) => ({
                          label: (m as any)?.name ?? String(m),
                          description: (m as any)?.description,
                          onClick: () => setModel(m as any),
                        }))
                      : []
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
                {loading ? (
                  <button
                    type="button"
                    className="p-2 text-background hover:text-background disabled:opacity-50"
                  >
                    <Square className=" p-1.5 w-6 aspect-auto fill-background bg-text/80 hover:bg-text rounded-full" />
                  </button>
                ) : (
                  <button
                    type="submit"
                    disabled={loading}
                    className="p-2 text-background hover:text-background disabled:opacity-50"
                  >
                    {/* <SendHorizontal className="w-5 h-5" /> */}
                    <svg
                      className="w-6 aspect-auto bg-text/80 hover:bg-text rounded-full"
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
