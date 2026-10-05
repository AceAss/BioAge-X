import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        bio: {
          bg: "#060913",
          surface: "#0c1322",
          card: "#111a2e",
          border: "#1e293b",
          primary: "#0ea5e9",
          secondary: "#14b8a6",
          accent: "#8b5cf6",
          accelerated: "#f43f5e",
          decelerated: "#10b981",
          synchronous: "#38bdf8",
        },
      },
      fontFamily: {
        sans: ["Inter", "-apple-system", "BlinkMacSystemFont", "Segoe UI", "sans-serif"],
        mono: ["JetBrains Mono", "Fira Code", "monospace"],
      },
      boxShadow: {
        glow: "0 0 25px -5px rgba(14, 165, 233, 0.25)",
        "glow-teal": "0 0 25px -5px rgba(20, 184, 166, 0.25)",
      },
    },
  },
  plugins: [],
};

export default config;
