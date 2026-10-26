import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#15232c",
        muted: "#667780",
        canvas: "#f5f8f7",
        teal: "#0d8b75",
      },
      boxShadow: {
        panel: "0 8px 30px rgba(28, 61, 57, .06)",
      },
    },
  },
  plugins: [],
};

export default config;
