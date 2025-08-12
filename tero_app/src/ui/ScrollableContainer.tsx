import React, {
  useRef,
  useEffect,
  useState,
  useCallback,
  type UIEvent,
  type ReactNode,
  type CSSProperties,
} from "react";

// Props
interface ChatScrollContainerProps {
  children: ReactNode;
  scrollCta: ReactNode;
  onScroll?: (e: UIEvent<HTMLDivElement>) => void;
  scrollRef: React.RefObject<HTMLDivElement | null> | null;
}

export const ChatScrollContainer: React.FC<ChatScrollContainerProps> = ({
  children,
  scrollCta,
  onScroll,
  scrollRef,
}) => {
  const outerDiv1 = useRef<HTMLDivElement | null>(null);
  const prevScrollTopRef = useRef<number>(0);
  const outerDiv = (scrollRef ?? outerDiv1) as React.RefObject<HTMLDivElement>;

  const [showScrollButton, setShowScrollButton] = useState(false);

  const handleScrollButtonClick = useCallback(() => {
    const el = outerDiv.current;
    if (!el) return;

    const outerDivHeight = el.clientHeight;

    el.scrollTo({
      top: outerDivHeight,
      left: 0,
      behavior: "smooth",
    });

    setShowScrollButton(false);
  }, [outerDiv]);

  const handleScroll = useCallback(
    (e: UIEvent<HTMLDivElement>) => {
      // Call any external onScroll handler
      onScroll?.(e);
      const { scrollHeight, scrollTop, clientHeight } = e.currentTarget;
      const scrollTopAbs = Math.abs(scrollTop);
      const prevScrollTop = prevScrollTopRef.current;

      // Show only when scrolling up, or from the top when you start scrolling down
      if (
        scrollTopAbs < prevScrollTop ||
        (prevScrollTop >= (scrollHeight * 90) / 100 &&
          scrollTopAbs > prevScrollTop)
      ) {
        if (scrollTopAbs > clientHeight) setShowScrollButton(true);
      }

      // Hide scroll button when at bottom of reversed content
      if (scrollTopAbs <= 50) {
        setShowScrollButton(false);
      }

      // Store current position for next scroll event
      prevScrollTopRef.current = scrollTopAbs;
    },
    [onScroll]
  );

  const buttonStyle: CSSProperties = {
    transform: "translateX(-50%)",
    opacity: showScrollButton ? 1 : 0,
    pointerEvents: showScrollButton ? "auto" : "none",
  };

  return (
    <div className="relative flex flex-col overflow-y-hidden">
      <div
        className="relative flex flex-col-reverse space-y-4 space-y-reverse h-fit max-h-fit overflow-y-auto no-scrollbar"
        onScroll={handleScroll}
        ref={outerDiv}
      >
        {children}
      </div>
      <button
        style={buttonStyle}
        className="absolute bottom-1 left-1/2 btn-text text-xs"
        onClick={handleScrollButtonClick}
      >
        {scrollCta}
      </button>
    </div>
  );
};

interface ScrollDivProps {
  children: ReactNode;
  className?: string;
  onBottomReach?: () => void;
}

export const ScrollDiv: React.FC<ScrollDivProps> = ({
  children,
  className,
  onBottomReach,
}) => {
  const scrollDiv = useRef<HTMLDivElement | null>(null);
  const [hasTriggered, setHasTriggered] = useState(false);

  useEffect(() => {
    // Reset trigger when children change (new content loaded)
    setHasTriggered(false);
  }, [children]);

  const handleScroll = useCallback(() => {
    const el = scrollDiv.current;
    if (el) {
      const { scrollTop, scrollHeight, clientHeight } = el;
      if (!hasTriggered && scrollTop + clientHeight >= scrollHeight * 0.8) {
        onBottomReach?.();
        setHasTriggered(true);
      }
    }
  }, [onBottomReach, hasTriggered]);

  return (
    <div
      ref={scrollDiv}
      className={`flex-1 overflow-y-auto h-full no-scrollbar ${
        className || ""
      }`}
      onScroll={handleScroll}
    >
      {children}
    </div>
  );
};
