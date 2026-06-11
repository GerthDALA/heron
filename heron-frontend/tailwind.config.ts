import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      colors: {
        heron: {
          teal: "#0F6E56",
          "teal-dark": "#085041",
          "teal-light": "#E1F5EE",
          danger: "#A32D2D",
          "danger-bg": "#FCEBEB",
          safe: "#3B6D11",
          "safe-bg": "#EAF3DE",
          amber: "#BA7517",
          "amber-bg": "#FAEEDA",
          neutral: "#2C2C2A",
          muted: "#5F5E5A",
          border: "#D3D1C7",
          surface: "#F1EFE8",
        },
      },
      fontFamily: {
        body: ["var(--font-body)"],
        mono: ["var(--font-mono)"],
      },
    },
  },
  plugins: [],
};
export default config;
