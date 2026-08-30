import type { Config } from "tailwindcss";

// Deliberately not the default Tailwind/shadcn palette (indigo/violet on
// white). This project reads as an intelligence/analysis tool, so the
// design leans into that: near-black surfaces, a signal-teal accent
// instead of the ubiquitous purple gradient, and a monospace type layer
// for anything that reads as "data" (IDs, timestamps, confidence scores).
const config: Config = {
  darkMode: "class",
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        background: "#0A0C0F",
        surface: "#12151A",
        "surface-raised": "#181C22",
        border: "#242931",
        "border-hover": "#343B46",
        foreground: "#E9EBEE",
        muted: "#8B92A0",
        "muted-foreground": "#6B7280",
        accent: {
          DEFAULT: "#2FD9C4",
          dim: "#1B8A7B",
          foreground: "#04211D",
        },
        signal: {
          high: "#34D399",
          medium: "#F5B93D",
          low: "#F0655A",
        },
      },
      fontFamily: {
        display: ["var(--font-display)", "system-ui", "sans-serif"],
        sans: ["var(--font-body)", "system-ui", "sans-serif"],
        mono: ["var(--font-mono)", "ui-monospace", "monospace"],
      },
      backgroundImage: {
        "grid-fade":
          "linear-gradient(to bottom, transparent, #0A0C0F 85%), linear-gradient(#242931 1px, transparent 1px), linear-gradient(90deg, #242931 1px, transparent 1px)",
      },
      backgroundSize: {
        grid: "100% 100%, 40px 40px, 40px 40px",
      },
      keyframes: {
        scan: {
          "0%": { transform: "translateY(-100%)" },
          "100%": { transform: "translateY(100%)" },
        },
        "pulse-dot": {
          "0%, 100%": { opacity: "1" },
          "50%": { opacity: "0.35" },
        },
        "fade-up": {
          "0%": { opacity: "0", transform: "translateY(8px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
      },
      animation: {
        scan: "scan 3.5s linear infinite",
        "pulse-dot": "pulse-dot 1.6s ease-in-out infinite",
        "fade-up": "fade-up 0.5s ease-out both",
      },
    },
  },
  plugins: [],
};

export default config;
