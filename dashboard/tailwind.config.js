/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ['"Inter"', 'system-ui', '-apple-system', 'sans-serif'],
      },
      colors: {
        bgPrimary: "#0b0f1a",
        bgCard: "#111827",
        accent: "#3b82f6",
        accentLight: "#60a5fa",
      },
      boxShadow: {
        card: "0 4px 24px 0 rgba(0,0,0,0.35)",
        cardHover: "0 8px 32px 0 rgba(59,130,246,0.12)",
        glowRed: "0 0 12px 2px rgba(239,68,68,0.35)",
      },
      backgroundImage: {
        'gradient-body': 'linear-gradient(135deg, #0b0f1a 0%, #111827 50%, #0f172a 100%)',
      },
    },
  },
  plugins: [],
}