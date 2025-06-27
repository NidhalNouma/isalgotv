import {
  useRef,
  useEffect,
  useState,
  useCallback,
  useLayoutEffect,
  Fragment,
} from "react";

export const ScrollContainer = ({
  children,
  scrollCta,
  onScroll,
  scrollRef,
}) => {
  const outerDiv1 = useRef(null);
  const outerDiv = scrollRef || outerDiv1;

  const prevInnerDivHeight = useRef(null);

  const [showMessages, setShowMessages] = useState(false);
  const [showScrollButton, setShowScrollButton] = useState(false);

  //   useLayoutEffect(() => {
  //     const outerDivHeight = outerDiv.current.clientHeight;
  //     const innerDivHeight = innerDiv.current.clientHeight;

  //     if (showMessages) {
  //       outerDiv.current.scrollTo({
  //         top: innerDivHeight - outerDivHeight,
  //         left: 0,
  //         behavior: "auto",
  //       });
  //       setShowScrollButton(false);
  //     }
  //   }, [showMessages]);

  //   useEffect(() => {
  //     const outerDivHeight = outerDiv.current.clientHeight;
  //     const innerDivHeight = innerDiv.current.clientHeight;
  //     const outerDivScrollTop = outerDiv.current.scrollTop;

  //     if (
  //       !prevInnerDivHeight.current ||
  //       outerDivScrollTop === prevInnerDivHeight.current - outerDivHeight
  //     ) {
  //       outerDiv.current.scrollTo({
  //         top: innerDivHeight - outerDivHeight,
  //         left: 0,
  //         behavior: prevInnerDivHeight.current ? "smooth" : "auto",
  //       });
  //       setShowMessages(true);
  //     } else if (outerDivScrollTop + outerDivHeight < innerDivHeight) {
  //       setShowScrollButton(true);
  //     }

  //     prevInnerDivHeight.current = innerDivHeight;
  //   }, [children]);

  const handleScrollButtonClick = useCallback(() => {
    const outerDivHeight = outerDiv.current.clientHeight;

    outerDiv.current.scrollTo({
      top: outerDivHeight,
      left: 0,
      behavior: "smooth",
    });

    setShowScrollButton(false);
  }, []);

  return (
    <div className="relative flex flex-col overflow-y-hidden">
      <div
        className="relative flex flex-col-reverse space-y-3 space-y-reverse h-fit max-h-fit overflow-y-auto scrollbar-hide"
        onScroll={(e) => {
          // Call any external onScroll handler
          if (onScroll) onScroll(e);
          const { scrollHeight, scrollTop, clientHeight } = e.target;

          // Hide scroll button when scrolled to bottom
          if (scrollHeight - scrollTop <= clientHeight + 20) {
            setShowScrollButton(false);
          }
        }}
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
        className="absolute bottom-1 left-1/2 btn-text transition-all duration-300"
        onClick={handleScrollButtonClick}
      >
        {scrollCta}
      </button>
    </div>
  );
};
