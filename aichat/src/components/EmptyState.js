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
      "Suggest a promising stock to watch this week.",
      "What are some potential short-selling opportunities in the market?",
      "Provide a trading idea based on recent market volatility.",
      "Are there any undervalued stocks in the tech sector?",
    ],
  },
  {
    label: "Technical Analysis",
    icon: (className) => <ChartNoAxesColumn className={` ${className}`} />,
    options: [
      "Analyze the chart of Apple Inc. (AAPL) using technical indicators.",
      "What does the RSI indicate for Tesla stock?",
      "Is there a head and shoulders pattern forming in the S&P 500?",
      "Can you perform a Fibonacci retracement analysis on Amazon stock?",
    ],
  },
  {
    label: "Learning Strategies",
    icon: (className) => <LibraryBig className={` ${className}`} />,
    options: [
      "Suggest a day trading strategy for volatile markets.",
      "How can I implement a swing trading strategy?",
      "What’s a good scalping strategy for forex trading?",
      "Explain how to use moving averages in trading strategies.",
    ],
  },
  {
    label: "Market News Updates",
    icon: (className) => <Newspaper className={` ${className}`} />,
    options: [
      "How do geopolitical tensions affect commodity prices?",
      "What is the impact of the latest Fed meeting on the markets?",
      "How do employment reports influence forex trading?",
      "Analyze the market reaction to the latest earnings season.",
    ],
  },
  {
    label: "Risk Management",
    icon: (className) => <Calculator className={` ${className}`} />,
    options: [
      "How can I manage risk in my trading portfolio?",
      "What is the importance of stop-loss orders?",
      "Explain position sizing and its role in risk management.",
      "How do I calculate the risk-reward ratio for a trade?",
    ],
  },
  {
    label: "Trading Psychology",
    icon: (className) => <Brain className={` ${className}`} />,
    options: [
      "How can I overcome fear and greed in trading?",
      "Tips for maintaining discipline in trading.",
      "How does emotional bias affect trading decisions?",
      "Strategies to manage stress in high-frequency trading.",
    ],
  },
  {
    label: "Pine Script Wizardry",
    icon: (className) => <Code className={` ${className}`} />,
    options: [
      "Help me code a custom moving average crossover strategy in Pine Script.",
      "How do I create an RSI indicator with alerts in Pine Script?",
      "Can you write a Pine Script for a Bollinger Bands breakout strategy?",
      "Assist me in coding a MACD histogram indicator in Pine Script.",
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
