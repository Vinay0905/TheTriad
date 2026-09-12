/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        background: "#0a0e16",
        surface: "#0f131c",
        surfaceHover: "#181c24",
        border: "#262a33",
        "surface-container": "#1c2028",
        "surface-container-high": "#262a33",
        "surface-container-highest": "#31353e",
        primary: "#4cd7f6",
        "primary-container": "#06b6d4",
        secondary: "#e3c198",
        tertiary: "#d0bcff",
        "on-surface": "#dfe2ee",
        "on-surface-variant": "#bcc9cd",
      },
      fontFamily: {
        headline: ["Plus Jakarta Sans", "sans-serif"],
        body: ["Inter", "sans-serif"],
        mono: ["JetBrains Mono", "monospace"],
      },
    },
  },
  plugins: [],
}
