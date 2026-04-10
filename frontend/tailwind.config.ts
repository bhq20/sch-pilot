import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        bhq: {
          primary: "#0B3D5C",
          accent: "#1F6491",
          light: "#F2F6FA",
          dim: "#6B7C8C",
          success: "#059669",
          danger: "#DC2626",
        },
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
      },
    },
  },
  plugins: [],
};
export default config;
