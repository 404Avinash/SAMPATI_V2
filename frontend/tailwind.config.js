export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        ink: {
          900: "#0b1f3a",
          800: "#122a4d",
          700: "#193860",
        },
        saffron: {
          DEFAULT: "#c8641e",
          light: "#e08a3e",
        },
        surface: {
          DEFAULT: "#ffffff",
          muted: "#f4f6fa",
        },
        hairline: "#e1e6ee",
        body: "#1c2b3f",
        muted: "#5b6b80",
        verdict: {
          allow: "#0f7a3d",
          allowBg: "#e7f6ec",
          hold: "#a8660a",
          holdBg: "#fdf1de",
          block: "#b3261e",
          blockBg: "#fce8e6",
        },
      },
      fontFamily: {
        serif: ["Source Serif 4", "Georgia", "serif"],
        sans: ["Inter", "system-ui", "sans-serif"],
        mono: ["IBM Plex Mono", "monospace"],
      },
      boxShadow: {
        glow: "0 0 24px rgba(200,100,30,0.35)",
        "glow-red": "0 0 28px rgba(179,38,30,0.45)",
        "glow-green": "0 0 20px rgba(15,122,61,0.35)",
      },
      keyframes: {
        pulseRing: {
          "0%, 100%": { opacity: 1, transform: "scale(1)" },
          "50%": { opacity: 0.6, transform: "scale(1.06)" },
        },
        scan: {
          "0%": { backgroundPosition: "0 0" },
          "100%": { backgroundPosition: "0 -200px" },
        },
      },
      animation: {
        "pulse-ring": "pulseRing 1.8s ease-in-out infinite",
        scan: "scan 6s linear infinite",
      },
    },
  },
  plugins: [],
};
