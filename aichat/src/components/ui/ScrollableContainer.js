import {
  useRef,
  useEffect,
  useState,
  useCallback,
  useLayoutEffect,
  Fragment,
} from "react";

export const ChatScrollContainer = ({
  children,
  scrollCta,
  onScroll,
  scrollRef,
}) => {
  const outerDiv1 = useRef(null);
  const prevScrollTopRef = useRef(0);
  const outerDiv = scrollRef || outerDiv1;

  const [showScrollButton, setShowScrollButton] = useState(false);

  const handleScrollButtonClick = useCallback(() => {
    const outerDivHeight = outerDiv.current.clientHeight;

    outerDiv.current.scrollTo({
      top: outerDivHeight,
      left: 0,
      behavior: "smooth",
    });

    setShowScrollButton(false);
  }, []);

  const handleScroll = useCallback(
    (e) => {
      // Call any external onScroll handler
      if (onScroll) onScroll(e);
      const { scrollHeight, scrollTop, clientHeight } = e.target;
      let scrollTopAbs = Math.abs(scrollTop);
      const prevScrollTop = prevScrollTopRef.current;

      //   console.log("scroll --- ", scrollTopAbs, prevScrollTop);

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

  return (
    <div className="relative flex flex-col overflow-y-hidden">
      <div
        className="relative flex flex-col-reverse space-y-4 space-y-reverse h-fit max-h-fit overflow-y-auto scrollbar-hide"
        onScroll={handleScroll}
        ref={outerDiv}
      >
        {children}
      </div>
      <button
        style={{
          transform: "translateX(-50%)",
          opacity: showScrollButton ? 1 : 0,
          pointerEvents: showScrollButton ? "auto" : "none",
        }}
        className="absolute bottom-1 left-1/2 btn-text "
        onClick={handleScrollButtonClick}
      >
        {scrollCta}
      </button>
    </div>
  );
};

export const ScrollDiv = ({ children, className, onBottomReach }) => {
  const scrollDiv = useRef(null);
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
        onBottomReach && onBottomReach();
        setHasTriggered(true);
      }
    }
  }, [onBottomReach, hasTriggered]);

  return (
    <div
      ref={scrollDiv}
      className={`flex-1 overflow-y-auto ${className || ""}`}
      onScroll={handleScroll}
    >
      {children}
    </div>
  );
};
