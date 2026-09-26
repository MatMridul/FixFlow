/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        samsung: {
          bg: "#0B0E14",
          surface: "#111622",
          card: "rgba(22, 28, 42, 0.75)",
          border: "rgba(255, 255, 255, 0.08)",
          blue: "#2B7FFF",
          "blue-glow": "rgba(43, 127, 255, 0.25)",
          emerald: "#10B981",
          amber: "#F59E0B",
          rose: "#EF4444",
        }
      },
      fontFamily: {
        sans: ["Inter", "-apple-system", "BlinkMacSystemFont", "Segoe UI", "Roboto", "sans-serif"],
      },
      boxShadow: {
        oneui: "0 8px 32px 0 rgba(0, 0, 0, 0.45)",
        "blue-glow": "0 0 24px -4px rgba(43, 127, 255, 0.4)",
      }
    },
  },
  plugins: [],
}
