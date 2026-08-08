import type { Config } from "tailwindcss";

/**
 * Ethereal Light — a premium daytime celestial palette, tuned to WCAG AAA.
 *
 * Every colour used for text clears 7:1 against white (AAA for normal text).
 * The measured ratios are recorded beside each token so a future edit cannot
 * quietly wash the interface out again:
 *
 *   ink     #0F172A  17.0:1
 *   ink-2   #334155  10.3:1
 *   ink-3   #475569   7.4:1   <- the floor for any text
 *   ink-4   #64748B   4.8:1   <- NOT for text; hairlines and strokes only
 *   gold    #6B4708   8.3:1
 *   nebula  #5B2E9D   9.1:1
 *   pos     #0F5233   9.0:1
 *   neg     #8F1E16   8.9:1
 *
 * Bright variants exist only as fills, rings and glows, never as type.
 */
const config: Config = {
  content: ["./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        // Grounds
        paper: "#F8FAFC", // page
        vellum: "#FFFFFF", // panels
        wash: "#F1F5F9", // alternating surfaces
        mist: "#E2E8F0",

        // Ink — all AAA except ink-4, which is barred from text
        ink: {
          DEFAULT: "#0F172A",
          2: "#334155",
          3: "#475569",
          4: "#64748B",
        },

        // Hairlines
        hair: {
          DEFAULT: "#E2E8F0",
          strong: "#CBD5E1",
        },

        // Accents
        gold: {
          DEFAULT: "#6B4708", // text / strokes
          bright: "#D8A33C", // fills, rings, glows
          wash: "#FDF6E7",
        },
        nebula: {
          DEFAULT: "#5B2E9D",
          bright: "#8B5CD6",
          wash: "#F3EDFC",
        },
        pos: { DEFAULT: "#0F5233", wash: "#E3F3EA" }, // 9.0:1 white, 8.2:1 on wash
        neg: { DEFAULT: "#8F1E16", wash: "#FCEBE9" }, // 8.9:1 white, 7.7:1 on wash
        retro: "#8F1E16",
      },
      fontFamily: {
        serif: ["var(--font-serif)", "Georgia", "serif"],
        mono: ["var(--font-mono)", "ui-monospace", "monospace"],
        sans: ["var(--font-sans)", "system-ui", "sans-serif"],
      },
      fontSize: {
        // Rebased upward. Body is 17px; nothing carrying prose sits below 15px,
        // and 13px is reserved for genuine micro-labels.
        micro: ["0.8125rem", { lineHeight: "1.15rem", letterSpacing: "0.04em" }],
        meta: ["0.9375rem", { lineHeight: "1.5rem" }],
        base: ["1.0625rem", { lineHeight: "1.7rem" }],
        lg: ["1.1875rem", { lineHeight: "1.8rem" }],
        xl: ["1.4375rem", { lineHeight: "1.95rem" }],
        "2xl": ["1.8125rem", { lineHeight: "2.25rem" }],
        "3xl": ["2.375rem", { lineHeight: "2.7rem" }],
        "4xl": ["3.125rem", { lineHeight: "3.3rem" }],
      },
      maxWidth: { shell: "1400px" },
      boxShadow: {
        panel:
          "0 1px 2px rgba(15,23,42,.06), 0 4px 12px -2px rgba(15,23,42,.08), 0 12px 32px -12px rgba(15,23,42,.10)",
        lift: "0 2px 6px rgba(15,23,42,.08), 0 18px 44px -16px rgba(15,23,42,.20)",
        glow: "0 0 0 1px rgba(216,163,60,.45), 0 6px 22px -6px rgba(216,163,60,.40)",
      },
      keyframes: {
        spinSlow: { to: { transform: "rotate(360deg)" } },
        breathe: { "0%,100%": { opacity: "0.75" }, "50%": { opacity: "1" } },
      },
      animation: {
        "spin-slow": "spinSlow 260s linear infinite",
        "spin-slower": "spinSlow 460s linear infinite reverse",
        breathe: "breathe 5s ease-in-out infinite",
      },
    },
  },
  plugins: [],
};

export default config;
