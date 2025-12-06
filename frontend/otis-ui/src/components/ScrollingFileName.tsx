import React, { useEffect, useRef, useState } from "react";

interface ScrollingFilenameProps {
  text: string;
  className?: string;
}

const ScrollingFilename: React.FC<ScrollingFilenameProps> = ({
  text,
  className = "",
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const measureRef = useRef<HTMLSpanElement>(null);
  const [shouldScroll, setShouldScroll] = useState(false);

  useEffect(() => {
    const container = containerRef.current;
    const measure = measureRef.current;

    if (container && measure) {
      const containerWidth = container.offsetWidth;
      const textWidth = measure.offsetWidth;

      setShouldScroll(textWidth > containerWidth);
    }
  }, [text]);

  return (
    <div
      ref={containerRef}
      className={`relative overflow-hidden group min-w-0 ${className}`}
      title={text}
    >
      {/* Hidden measuring span */}
      <span
        ref={measureRef}
        className="absolute whitespace-nowrap opacity-0 pointer-events-none"
      >
        {text}
      </span>

      {/* If overflow → marquee loop */}
      {shouldScroll && (
        <div className="whitespace-nowrap hidden group-hover:block">
          <div className="marquee">
            <span className="marquee__inner">{text}</span>
            <span className="marquee__inner">{text}</span>
          </div>
        </div>
      )}

      {/* Idle state → ALWAYS one line */}
      <p
        className={`whitespace-nowrap overflow-hidden ${
          shouldScroll ? "group-hover:hidden" : ""
        }`}
      >
        {text}
      </p>
    </div>
  );
};

export default ScrollingFilename;
