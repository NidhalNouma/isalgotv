import React from "react";
import { Award, Brain, ChartCandlestick, ChartArea } from "lucide-react";

function HeroSection({ className }) {
  return (
    <div
      className={
        "text-title max-w-5xl mx-auto my-auto text-center py-16 " + className
      }
    >
      <h1 className="text-4xl sm:text-5xl font-medium mb-6 tracking-tight leading-tight ">
        <span className="bg-gradient-to-r from-accent via-primary/70 to-primary bg-clip-text text-transparent animate-gradient-x">
          IsalGo AI
        </span>{" "}
        is Coming Soon!
      </h1>

      <p className="text-xl text-text mb-2 max-w-2xl mx-auto">
        Get ready to transform your trading experience with{" "}
        <span className="text-primary font-semibold">AI-crafted</span>{" "}
        strategies and insights.
      </p>
      <p className="text-sm text-text mb-8 max-w-md mx-auto">
        Sign up now, and we’ll notify you as soon as we launch!
      </p>

      <div className="flex flex-col sm:flex-row items-center justify-center space-y-4 sm:space-y-0 sm:space-x-4 mb-8">
        <a className="btn-primary-landing" href="/p/register">
          Notify Me at Launch
          <svg
            class="h-5 w-5 ml-2"
            stroke="currentColor"
            fill="currentColor"
            stroke-width="0"
            viewBox="0 0 256 256"
            xmlns="http://www.w3.org/2000/svg"
          >
            <path d="M84,16V12a12,12,0,0,1,24,0v4a12,12,0,0,1-24,0ZM16,108a12,12,0,0,0,0-24H12a12,12,0,0,0,0,24ZM128.2,39.38a12,12,0,0,0,15.18-7.59l4-12a12,12,0,0,0-22.76-7.58l-4,12A12,12,0,0,0,128.2,39.38Zm-104,81.24-12,4a12,12,0,1,0,7.58,22.76l12-4a12,12,0,1,0-7.58-22.76Zm197.93,60.55a20,20,0,0,1,0,28.29l-12.68,12.68a20,20,0,0,1-28.29,0l-45.51-45.51L118.54,216h0a19.81,19.81,0,0,1-18.27,12l-1,0a19.81,19.81,0,0,1-18-13.74L29,54.16A20,20,0,0,1,54.16,29L214.24,81.27A20,20,0,0,1,216,118.54l-39.37,17.12Zm-19.8,14.14L155.5,148.47A20,20,0,0,1,161.67,116l35-15.21L54.29,54.29l46.49,142.37,15.21-35A20,20,0,0,1,130.6,150a19.74,19.74,0,0,1,3.74-.36,20,20,0,0,1,14.13,5.86l46.84,46.84Z"></path>
          </svg>
        </a>
      </div>

      {/* <div className="flex flex-wrap justify-center items-center gap-8">
        <div className="flex items-center space-x-2">
          <Brain className="h-5 w-5 text-purple-500" />
          <span className="text-text/80">Customized AI Strategies</span>
        </div>
        <div className="flex items-center space-x-2">
          <Award className="h-5 w-5 text-primary" />
          <span className="text-text/80">Instant Expert Support</span>
        </div>
        <div className="flex items-center space-x-2">
          <ChartArea className="h-5 w-5 text-profit" />
          <span className="text-text/80">Simplified Chart Analysis</span>
        </div>
        <div className="flex items-center space-x-2">
          <ChartCandlestick className="h-5 w-5 text-accent" />
          <span className="text-text/80">Competitive Edge</span>
        </div>
      </div> */}
    </div>
  );
}

export default HeroSection;
