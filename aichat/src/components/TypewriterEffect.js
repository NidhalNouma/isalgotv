import React, { useState, useLayoutEffect, useRef, useEffect } from "react";
import AiResponseMarkdown from "./AiResponseMarkdown";

export default function TypewriterEffect({ content, onComplete }) {
  const [displayedContent, setDisplayedContent] = useState("");
  const [currentIndex, setCurrentIndex] = useState(0);

  const containerRef = useRef(null);
  const autoScrollEnabledRef = useRef(true);

  useLayoutEffect(() => {
    if (currentIndex < content.length) {
      const timeout = setTimeout(() => {
        setDisplayedContent((prev) => prev + content[currentIndex]);
        setCurrentIndex((prev) => prev + 1);

        // Ensure parent containers are scrolled to bottom
        const element = containerRef.current;
        if (element) {
          const scrollableParent = element.closest(".overflow-y-auto");
          if (scrollableParent && autoScrollEnabledRef.current) {
            scrollableParent.scrollTop = scrollableParent.scrollHeight;
          }
        }
      }, 1 + Math.random() * 5); // Varying speed for more natural effect

      return () => clearTimeout(timeout);
    } else if (onComplete) {
      onComplete();
    }
  }, [content, currentIndex, onComplete]);

  useEffect(() => {
    const element = containerRef.current;
    if (!element) return;
    const scrollableParent = element.closest(".overflow-y-auto");
    if (!scrollableParent) return;

    const handleScroll = () => {
      const atBottom =
        scrollableParent.scrollHeight -
          scrollableParent.clientHeight -
          scrollableParent.scrollTop <
        5;
      autoScrollEnabledRef.current = atBottom;
    };

    scrollableParent.addEventListener("scroll", handleScroll);
    handleScroll();
    return () => {
      scrollableParent.removeEventListener("scroll", handleScroll);
    };
  }, []);

  return (
    <div ref={containerRef}>
      <AiResponseMarkdown message={displayedContent} />
    </div>
  );
}
