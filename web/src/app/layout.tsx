import type { Metadata, Viewport } from "next";
import { Inter, JetBrains_Mono, Playfair_Display } from "next/font/google";
import CelestialField from "@/components/CelestialField";
import "./globals.css";

/**
 * Fonts are fetched at build time and served from this origin, so the running
 * page makes no third-party request — matching the Python app's
 * `default-src 'self'` policy.
 */
const serif = Playfair_Display({
  subsets: ["latin"],
  weight: ["400", "500", "600"],
  variable: "--font-serif",
  display: "swap",
});

const mono = JetBrains_Mono({
  subsets: ["latin"],
  weight: ["400", "500"],
  variable: "--font-mono",
  display: "swap",
});

const sans = Inter({
  subsets: ["latin"],
  variable: "--font-sans",
  display: "swap",
});

export const metadata: Metadata = {
  title: "KOSMA — Living Cosmos",
  description:
    "A Vedic chart computed to the arc-second, showing only what it can support.",
  robots: { index: false, follow: false },
};

export const viewport: Viewport = {
  themeColor: "#FAF9F6",
  colorScheme: "light",
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html
      lang="en"
      className={`${serif.variable} ${mono.variable} ${sans.variable}`}
    >
      <body className="min-h-screen">
        <CelestialField />

        {/* The shell runs to 92% of the viewport, capped at 1400px, so wide
            displays get a genuine multi-column layout instead of a column of
            cards down the middle. */}
        <div className="relative z-10 mx-auto flex min-h-screen w-[92%] max-w-shell flex-col pb-28 pt-8">
          <header className="mb-10 flex flex-wrap items-end justify-between gap-x-8 gap-y-3 border-b border-slate-300 pb-5">
            <div className="flex flex-wrap items-baseline gap-x-6 gap-y-2">
              <a
                href="/"
                className="heading text-2xl font-semibold tracking-[0.26em] text-ink"
              >
                KOSMA
                <span className="text-gold-bright">.</span>
              </a>
              <nav className="flex gap-1.5">
                <a
                  href="/"
                  className="rounded-lg border border-slate-300 bg-white px-3 py-1.5 font-mono text-micro font-bold text-ink-2 transition-all hover:border-gold hover:bg-gold-wash hover:text-gold"
                >
                  Chart
                </a>
                <a
                  href="/compare"
                  className="rounded-lg border border-slate-300 bg-white px-3 py-1.5 font-mono text-micro font-bold text-ink-2 transition-all hover:border-gold hover:bg-gold-wash hover:text-gold"
                >
                  Compare
                </a>
              </nav>
            </div>
            <span className="eyebrow-quiet">
              Lahiri sidereal &middot; Swiss Ephemeris &middot; nothing stored
            </span>
          </header>

          <main className="flex-1">{children}</main>

          <footer className="mt-24 border-t border-slate-300 pt-6 text-center">
            <p className="eyebrow-quiet mb-2">
              Computed in memory and discarded &middot; no database &middot; no cookies
            </p>
            <p className="text-meta text-ink-3">
              For reflection. Not medical, legal, financial, or psychological advice.
            </p>
          </footer>
        </div>
      </body>
    </html>
  );
}
