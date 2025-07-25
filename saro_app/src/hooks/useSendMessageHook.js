import { useState, useEffect, useRef } from "react";
import { useUser } from "../contexts/UserContext";

import { AI_MODELS } from "../constant";

export function SendMessageHook(onSend, disabled, toggleAuthPopup) {
  const { user } = useUser();

  const [input, setInput] = useState("");
  const [files, setFiles] = useState([]);

  const [model, setModel] = useState(AI_MODELS[0]);

  const fileInputRef = useRef(null);
  const textareaRef = useRef(null);

  useEffect(() => {
    function handleDjangoMessage(e) {
      console.log("Received message:", e.detail.message);
      handleSubmit(null, e.detail.message);
    }
    window.addEventListener("saroMessage", handleDjangoMessage);
    return () => {
      window.removeEventListener("saroMessage", handleDjangoMessage);
    };
  }, [user]);

  const handleSubmit = async (e, message = null) => {
    e?.preventDefault();

    let msg = input.trim() || message;

    console.log("Submitting message:", msg, user);

    if ((msg || files.length > 0) && !disabled) {
      if (!user) {
        toggleAuthPopup();
        // setInput("");
        return;
      }

      await onSend(msg, files, model);
      setInput("");
      setFiles([]);
      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }
      if (textareaRef.current) {
        textareaRef.current.style.height = "auto";
      }
    }
  };

  const handleFileChange = (e) => {
    if (e.target.files) {
      setFiles(Array.from(e.target.files));
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  const handleInput = (e) => {
    const textarea = e.target;
    setInput(textarea.value);
    textarea.style.height = "auto";
    textarea.style.height = `${textarea.scrollHeight}px`;
  };

  return {
    input,
    files,
    fileInputRef,
    textareaRef,
    setInput,
    setFiles,
    handleSubmit,
    handleFileChange,
    handleKeyDown,
    handleInput,

    models: AI_MODELS,
    model,
    setModel,
  };
}
