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
  Workflow,
  Bell,
} from "lucide-react";

import ChatInput from "./ChatInput";

const titles = [
  "Ready when you are.",
  "What can I help with?",
  "How can I assist you today?",
  "What trading insights are you looking for?",
  "Need help with trading strategies?",
  "Looking for market analysis?",
  "Want to learn about trading techniques?",
  "Have questions about risk management?",
  "Curious about trading psychology?",
  "Interested in Pine Script coding?",
  "Thinking about automating trades?",
  "Need help writing alerts?",
];

export default function EmptyState({ onSendMessage }) {
  const [quickActionMsg, setQuuickActionMsg] = useState(null);
  const [title] = useState(titles[Math.floor(Math.random() * titles.length)]);

  return (
    <div className="flex-1 flex flex-col items-center justify-center md:px-4 px-1 h-full">
      <h1 className="text-4xl font-semibold mb-8 text-title text-center">
        {/* What can I help with? */}
        {title}
      </h1>

      <div className="w-full max-w-3xl mx-auto">
        <ChatInput
          onSend={onSendMessage}
          className=""
          quickActionMsg={quickActionMsg}
          // focus={true}
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
      "Suggest a profitable trading strategy for the current market conditions.",
      "What are some high-probability trade setups for this week?",
      "Analyze recent market volatility and suggest a trading opportunity.",
      "Are there any undervalued assets that could offer good returns?",
    ],
  },
  {
    label: "Technical Analysis",
    icon: (className) => <ChartNoAxesColumn className={` ${className}`} />,
    options: [
      "Perform a detailed technical analysis on Apple Inc. (AAPL).",
      "How does the RSI indicator look for Tesla stock right now?",
      "Identify any key support and resistance levels in the S&P 500.",
      "Can you provide a Fibonacci retracement analysis for Amazon?",
    ],
  },
  {
    label: "Learning Strategies",
    icon: (className) => <LibraryBig className={` ${className}`} />,
    options: [
      "Explain a robust day trading strategy for high-volatility markets.",
      "How do I develop a systematic swing trading strategy?",
      "What’s an effective scalping strategy for forex trading?",
      "Break down the use of moving averages in trading strategies.",
    ],
  },
  {
    label: "Risk Management",
    icon: (className) => <Calculator className={` ${className}`} />,
    options: [
      "How do I manage risk effectively in my trading portfolio?",
      "Why are stop-loss orders crucial in trading?",
      "Explain the concept of position sizing in risk management.",
      "How can I calculate and optimize the risk-reward ratio for my trades?",
    ],
  },
  {
    label: "Trading Psychology",
    icon: (className) => <Brain className={` ${className}`} />,
    options: [
      "What are the best techniques to overcome fear and greed in trading?",
      "How can I develop more discipline in my trading approach?",
      "Explain how emotional bias affects trading decisions.",
      "What strategies can I use to manage stress in high-frequency trading?",
    ],
  },
  {
    label: "Pine Script Wizardry",
    icon: (className) => <Code className={` ${className}`} />,
    options: [
      "Help me code a moving average crossover strategy in Pine Script v6.",
      "How do I create an RSI indicator with alerts in Pine Script?",
      "Can you write a Pine Script for a Bollinger Bands breakout strategy?",
      "Assist me in coding a MACD histogram indicator with custom settings.",
    ],
  },
  {
    label: "Automating Trades",
    icon: (className) => <Workflow className={` ${className}`} />,
    options: [
      "How do I automate my TradingView strategy using IsAlgo Automate?",
      "Can you format a TradingView alert message for IsAlgo automation?",
      "What placeholders should I use in IsAlgo Alerts?",
      "How does the Automation Playground help in testing my alerts?",
    ],
  },
  {
    label: "Writing Alerts",
    icon: (className) => <Bell className={` ${className}`} />,
    options: [
      "Can you generate a TradingView alert message using IsAlgo Alerts Placeholders?",
      "Format an alert message for a buy signal using IsAlgo Alerts.",
      "How do I structure an alert message for automated trading?",
      "Can you give me an example of a stop-loss alert using IsAlgo placeholders?",
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
