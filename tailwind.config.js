/** @type {import('tailwindcss').Config} */
const colors = require("tailwindcss/colors");

module.exports = {
  darkMode: "class",
  content: [
    "./templates/**/*.html",
    "./etradingview/templates/**/*.html",
    "./strategies/templates/**/*.html",
    "./profile_user/templates/**/*.html",
    "./docs/templates/**/*.html",
    "./aichat/src/**/*.js",
    "./aichat/src/components/**/*.js",

    "./node_modules/flowbite/**/*.js",
  ],
  theme: {
    colors: {
      // primary : { dark: "hsl(265, 100%, 35%);", light: "hsl(265, 100%, 35%);" },
      // secondary : { dark: "hsl(178, 97.9%, 26.7%);" , light: "hsl(178, 97.9%, 26.7%);" },
      // accent : { dark: "hsl(58, 75%, 40%);", light: "hsl(58, 75%, 40%);" },
      // background : { dark: "hsl(188, 16%, 17%);", light: "hsl(188, 16%, 92%);" },
      // text : { dark: "hsl(0, 0%, 90%);", light: "hsl(0, 0%, 20%);" },
      // title : { dark: "hsl(0, 0%, 100%);", light: "hsl(0, 0%, 0%);" },

      primary: "hsl(var(--color-primary) / <alpha-value>)",
      secondary: "hsl(var(--color-secondary) / <alpha-value>)",
      accent: "hsl(var(--color-accent) / <alpha-value>)",
      background: "hsl(var(--color-background) / <alpha-value>)",
      text: "hsl(var(--color-text) / <alpha-value>)",
      "text-light": "hsl(var(--color-text-light) / <alpha-value>)",
      title: "hsl(var(--color-title) / <alpha-value>)",
      "title-light": "hsl(var(--color-title-light) / <alpha-value>)",
      profit: "hsl(var(--color-profit) / <alpha-value>)",
      loss: "hsl(var(--color-loss) / <alpha-value>)",
      // success : "",
      // info : "",
      // warning : "",
      // danger : "",
      transparent: "transparent",
      current: "currentColor",
      black: colors.black,
      white: colors.white,
      gray: colors.gray,
      emerald: colors.emerald,
      indigo: colors.indigo,
      yellow: colors.yellow,
    },
    extend: {
      keyframes: {
        "rotate-gradient": {
          "0%": { "--gradient-angle": "0deg" },
          "100%": { "--gradient-angle": "360deg" },
        },

        animate: {
          "0%,10%,100%": { width: "0%" },
          "70%,80%,90%": { width: "100%" },
        },
        rotateGradient: {
          "0%": { "background-position": "0% 50%" },
          "50%": { "background-position": "100% 50%" },
          "100%": { "background-position": "0% 50%" },
        },
      },
      animation: {
        animate: "animate 6s linear",
        "rotate-gradient": "rotate-gradient 5s linear infinite",

        rotateGradient: "rotateGradient 8s ease-in-out infinite",
        rotateGradientSlow: "rotateGradient 12s ease-in-out infinite",
        rotateGradientFast: "rotateGradient 4s ease-in-out infinite",
      },
    },
  },
  safelist: [
    "scale-0",
    "scale-100",
    "transition-transform",
    "duration-200",
    "ease-out",
  ],
  plugins: [require("flowbite/plugin"), require("@tailwindcss/line-clamp")],
};
