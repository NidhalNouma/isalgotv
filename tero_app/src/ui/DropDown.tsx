import { useState, useRef, useLayoutEffect, useEffect, Fragment } from "react";

import { ChevronDown } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

interface DropdownOption {
  label: string;
  description?: string;
  onClick: () => void;
}

interface DropdownProps {
  className?: string;
  btnClassName?: string;
  defaultLabel?: string;
  children?: React.ReactNode;
  options: DropdownOption[];
  disabled?: boolean;
}

export function Dropdown({
  className,
  btnClassName,
  defaultLabel,
  options,
  disabled = false,
}: DropdownProps) {
  const [open, setOpen] = useState<boolean>(false);
  const [label, setLabel] = useState<string>(defaultLabel || "Select an option");
  const [dropUp, setDropUp] = useState<boolean>(false);
  const [dropdownMaxHeight, setDropdownMaxHeight] = useState<number | null>(null);
  const containerRef = useRef<HTMLDivElement | null>(null);
  const dropdownRef = useRef<HTMLDivElement | null>(null);

  const toggleOpen = () => setOpen((o) => !o);

  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  useLayoutEffect(() => {
    if (open && containerRef.current && dropdownRef.current) {
      const rect = containerRef.current.getBoundingClientRect();
      const dropdownRect = dropdownRef.current.getBoundingClientRect();
      const spaceBelow = window.innerHeight - rect.bottom;
      const spaceAbove = rect.top;

      const shouldDropUp =
        spaceBelow < dropdownRect.height && spaceAbove > spaceBelow;
      setDropUp(shouldDropUp);

      const availableHeight = shouldDropUp ? spaceAbove - 20 : spaceBelow - 20;
      setDropdownMaxHeight(availableHeight);
    }
  }, [open]);

  return (
    <div
      ref={containerRef}
      className={`relative inline-block text-left ${className}`}
    >
      <button
        className={`${btnClassName} disabled:opacity-50 flex items-center justify-between`}
        onClick={toggleOpen}
        type="button"
        disabled={disabled}
      >
        {label} <ChevronDown className="w-4 aspect-auto ml-1" />
      </button>
      <AnimatePresence>
        {open && (
          <Fragment>
            <motion.div
              ref={dropdownRef}
              initial={{ opacity: 0, y: dropUp ? 10 : -10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: dropUp ? 10 : -10 }}
              className={`absolute left-0 w-fit min-w-full bg-background/70 z-40 rounded-md no-scrollbar ${
                dropUp ? "bottom-full mb-2" : "top-full mt-2"
              }`}
              style={{
                maxHeight: dropdownMaxHeight || "auto",
                overflowY: "auto",
              }}
            >
              <ul className="py-1 bg-text/20 backdrop-blur-3xl rounded-md">
                {options.map((option, index) => (
                  <li
                    key={index}
                    className="px-4 py-2 text-text text-xs hover:bg-text/10 cursor-pointer"
                    onClick={() => {
                      setLabel(option.label);
                      option.onClick();
                      setOpen(false);
                    }}
                  >
                    {option.label}
                    {option?.description && (
                      <Fragment>
                        <br />
                        <p className="text-text/60 text-xs truncate">
                          {option.description}
                        </p>
                      </Fragment>
                    )}
                  </li>
                ))}
              </ul>
            </motion.div>
          </Fragment>
        )}
      </AnimatePresence>
    </div>
  );
}
