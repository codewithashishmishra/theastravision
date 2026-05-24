import type { Config } from "tailwindcss";
import { nextui } from "@nextui-org/react";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
    "./node_modules/@nextui-org/theme/dist/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {},
  },
  darkMode: "class",
  plugins: [nextui({
    themes: {
      light: {
        colors: {
          background: "#f9fafb",
          foreground: "#111827",
          primary: {
            DEFAULT: "#f97316",
            foreground: "#ffffff",
          },
          focus: "#f97316",
          content1: "#ffffff",
          divider: "#e5e7eb",
        },
      },
      dark: {
        colors: {
          background: "#030712",
          foreground: "#f9fafb",
          primary: {
            DEFAULT: "#f97316",
            foreground: "#ffffff",
          },
          focus: "#f97316",
          content1: "#111827",
          content2: "#1f2937",
          divider: "#1f2937",
        },
      },
    },
  })],
};

export default config;
