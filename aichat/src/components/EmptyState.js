import { Fragment, useState, useEffect, useRef } from "react";
import {
  ChartNoAxesColumn,
  Newspaper,
  Lightbulb,
  Calculator,
  LibraryBig,
  Brain,
  Code,
  Bitcoin,
} from "lucide-react";

import Typewriter from "typewriter-effect";

import ChatInput from "./ChatInput";

export default function EmptyState({ onSendMessage }) {
  const [quickActionMsg, setQuuickActionMsg] = useState(null);

  return (
    <div className="flex-1 flex flex-col items-center justify-center px-4 h-full">
      <h1 className="text-4xl font-semibold mb-8 text-title ">
        {/* What can I help with? */}
        <Typewriter
          onInit={(typewriter) => {
            typewriter
              .typeString("What can I help with?")
              .callFunction(() => {
                const cursorElement = document.querySelector(
                  ".Typewriter__cursor"
                );
                if (cursorElement) {
                  cursorElement.style.display = "none";
                }
              })
              .start();
          }}
          options={{
            autoStart: true,
            delay: 50,
            deleteSpeed: Infinity,
          }}
        />
      </h1>

      <div className="w-full max-w-3xl mx-auto">
        <ChatInput
          onSend={onSendMessage}
          className="j"
          quickActionMsg={quickActionMsg}
        />
      </div>

      <QuickActions setQuuickActionMsg={setQuuickActionMsg} />
    </div>
  );
}

const QuickActionsArray = [
  {
    label: "Trading Ideas",
    icon: (className) => <Lightbulb className={` ${className}`} />,
    options: [
      "What’s the current trend in Bitcoin prices?",
      "How can I trade Ethereum effectively?",
      "Explain the risks involved in cryptocurrency trading.",
      "What are the best indicators for crypto technical analysis?",
    ],
  },
  {
    label: "Technical Analysis",
    icon: (className) => <ChartNoAxesColumn className={` ${className}`} />,
    options: [
      "What’s the current trend in Bitcoin prices?",
      "How can I trade Ethereum effectively?",
      "Explain the risks involved in cryptocurrency trading.",
      "What are the best indicators for crypto technical analysis?",
    ],
  },
  {
    label: "Learning Strategies",
    icon: (className) => <LibraryBig className={` ${className}`} />,
    options: [
      "What’s the current trend in Bitcoin prices?",
      "How can I trade Ethereum effectively?",
      "Explain the risks involved in cryptocurrency trading.",
      "What are the best indicators for crypto technical analysis?",
    ],
  },
  {
    label: "Market News Updates",
    icon: (className) => <Newspaper className={` ${className}`} />,
    options: [
      "What’s the current trend in Bitcoin prices?",
      "How can I trade Ethereum effectively?",
      "Explain the risks involved in cryptocurrency trading.",
      "What are the best indicators for crypto technical analysis?",
    ],
  },
  {
    label: "Risk Management",
    icon: (className) => <Calculator className={` ${className}`} />,
    options: [
      "What’s the current trend in Bitcoin prices?",
      "How can I trade Ethereum effectively?",
      "Explain the risks involved in cryptocurrency trading.",
      "What are the best indicators for crypto technical analysis?",
    ],
  },
  {
    label: "Trading Psychology",
    icon: (className) => <Brain className={` ${className}`} />,
    options: [
      "What’s the current trend in Bitcoin prices?",
      "How can I trade Ethereum effectively?",
      "Explain the risks involved in cryptocurrency trading.",
      "What are the best indicators for crypto technical analysis?",
    ],
  },
  {
    label: "Pine Script Wizardry",
    icon: (className) => <Code className={` ${className}`} />,
    options: [
      "What’s the current trend in Bitcoin prices?",
      "How can I trade Ethereum effectively?",
      "Explain the risks involved in cryptocurrency trading.",
      "What are the best indicators for crypto technical analysis?",
    ],
  },
  {
    label: "Cryptocurrency Trading",
    icon: (className) => <Bitcoin className={` ${className}`} />,
    options: [
      "What’s the current trend in Bitcoin prices?",
      "How can I trade Ethereum effectively?",
      "Explain the risks involved in cryptocurrency trading.",
      "What are the best indicators for crypto technical analysis?",
    ],
  },
];

function QuickActions({ setQuuickActionMsg }) {
  let iconClassName = "h-4 w-4";
  const [options, setOptions] = useState(null);

  const divRef = useRef(null);

  const handleClickOutside = (event) => {
    if (divRef.current && !divRef.current.contains(event.target)) {
      setOptions((prev) => (prev?.length > 0 ? null : prev));
    }
  };

  useEffect(() => {
    document.addEventListener("mousedown", handleClickOutside);
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, []);

  const [visibleItems, setVisibleItems] = useState([]);

  useEffect(() => {
    // Reveal each item one by one
    if (options?.length > 0)
      options?.forEach((_, i) => {
        setTimeout(() => {
          setVisibleItems((prevVisibleItems) => [...prevVisibleItems, i]);
        }, i * 100); // Adjust the delay between each item
      });
    else setVisibleItems([]);
  }, [options]);

  return options?.length > 0 ? (
    <Fragment>
      <div
        ref={divRef}
        className="grid grid-cols-1 gap-4 max-w-3xl w-full mx-auto px-6"
      >
        {options.map((v, i) => (
          <div
            key={i}
            className={`${
              i !== options.length - 1 && "border-none border-text/20"
            } transition-all duration-500 ease-out ${
              visibleItems.includes(i) ? "opacity-100" : "opacity-0"
            }  `}
          >
            <div
              onClick={() => setQuuickActionMsg(v)}
              className={`transition-all duration-200 ease-out  hover:bg-text/20 rounded-lg py-2 px-2 text-text/80 hover:text-text cursor-pointer `}
            >
              <p className="font-medium text-sm ">{v}</p>
            </div>
          </div>
        ))}
      </div>
    </Fragment>
  ) : (
    <Fragment>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 max-w-4xl w-full">
        {QuickActionsArray.map((v, i) => (
          <ActionButton
            key={i}
            label={v.label}
            icon={v.icon(iconClassName)}
            onClick={() => setOptions(v.options)}
          />
        ))}
      </div>
    </Fragment>
  );
}

function ActionButton({ key, icon, label, onClick }) {
  return (
    <button
      key={key}
      onClick={onClick}
      className="flex items-center gap-2 py-2 px-4 border border-text/20 rounded-3xl hover:bg-text/20 transition-colors text-left w-full"
    >
      <div className="text-text/60">{icon}</div>
      <div>
        <div className="font-medium text-sm text-text/80">{label}</div>
        {/* <div className="text-sm text-text/60">{description}</div> */}
      </div>
    </button>
  );
}
