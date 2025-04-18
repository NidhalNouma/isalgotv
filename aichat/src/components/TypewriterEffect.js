import React, { useState, useEffect, useRef } from "react";
import AiResponseMarkdown from "./AiResponseMarkdown";

export default function TypewriterEffect({ content, onComplete }) {
  const [displayedContent, setDisplayedContent] = useState("");
  const [currentIndex, setCurrentIndex] = useState(0);

  const containerRef = useRef(null);

  useEffect(() => {
    if (currentIndex < content.length) {
      const timeout = setTimeout(() => {
        setDisplayedContent((prev) => prev + content[currentIndex]);
        setCurrentIndex((prev) => prev + 1);

        // Ensure parent containers are scrolled to bottom
        const element = containerRef.current;
        if (element) {
          const scrollableParent = element.closest(".overflow-y-auto");
          if (scrollableParent) {
            scrollableParent.scrollTop = scrollableParent.scrollHeight;
          }
        }
      }, 1 + Math.random() * 20); // Varying speed for more natural effect

      return () => clearTimeout(timeout);
    } else if (onComplete) {
      onComplete();
    }
  }, [content, currentIndex, onComplete]);

  return <div ref={containerRef}>
    <AiResponseMarkdown message={displayedContent} />
  </div>;
}
