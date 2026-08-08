"use client";

import { create } from "zustand";
import { fetchChart } from "@/lib/api";
import type { BirthInput, ChartResponse, Planet } from "@/types/chart";

/**
 * One store, sliced so components subscribe only to what they draw.
 *
 * The chart object is replaced wholesale on load and never mutated, so the
 * heavy panels re-render once. Hover and selection live in their own fields:
 * moving the mouse across the chart changes `hoveredHouse` and nothing that
 * reads `chart` re-renders.
 */

interface ChartState {
  chart: ChartResponse | null;
  loading: boolean;
  error: string | null;

  /** Planet id whose drishti rays are drawn. Null means none. */
  activePlanet: string | null;
  /** House under the cursor, 1–12. */
  hoveredHouse: number | null;
  /** Julian day the timeline is scrubbed to; null means "now". */
  focusedJd: number | null;
  /** Houses a live remedy is notionally addressing, for the healing glow. */
  soothedHouses: number[];
  /** Which divisional chart the grid is drawing. "D1" is the rasi. */
  activeVarga: string;

  load: (input: BirthInput) => Promise<void>;
  setActivePlanet: (id: string | null) => void;
  setHoveredHouse: (house: number | null) => void;
  setFocusedJd: (jd: number | null) => void;
  sootheHouses: (houses: number[]) => void;
  setVarga: (code: string) => void;
  reset: () => void;
}

export const useChartStore = create<ChartState>((set) => ({
  chart: null,
  loading: false,
  error: null,
  activePlanet: null,
  hoveredHouse: null,
  focusedJd: null,
  soothedHouses: [],
  activeVarga: "D1",

  load: async (input) => {
    set({ loading: true, error: null });
    try {
      const chart = await fetchChart(input);
      set({
        chart,
        loading: false,
        activePlanet: null,
        focusedJd: null,
        activeVarga: "D1",
      });
    } catch (err) {
      set({
        loading: false,
        error: err instanceof Error ? err.message : "Could not compute the chart.",
      });
    }
  },

  setActivePlanet: (id) =>
    set((s) => ({ activePlanet: s.activePlanet === id ? null : id })),
  setHoveredHouse: (house) => set({ hoveredHouse: house }),
  setFocusedJd: (jd) => set({ focusedJd: jd }),
  sootheHouses: (houses) => set({ soothedHouses: houses }),
  // Drishti is computed in the rasi, so switching division clears the traced
  // planet rather than drawing D1 aspects over a D9 grid.
  setVarga: (code) => set({ activeVarga: code, activePlanet: null }),
  reset: () =>
    set({
      chart: null,
      error: null,
      activePlanet: null,
      hoveredHouse: null,
      focusedJd: null,
      soothedHouses: [],
      activeVarga: "D1",
    }),
}));

/* ── Selectors ──────────────────────────────────────────────────────── */

export const selectPlanetsByHouse = (chart: ChartResponse | null) => {
  const byHouse = new Map<number, Planet[]>();
  if (!chart) return byHouse;
  for (const p of chart.planets) {
    const list = byHouse.get(p.house_index) ?? [];
    list.push(p);
    byHouse.set(p.house_index, list);
  }
  return byHouse;
};

/** House index (1–12) for a sign, counted whole-sign from the lagna. */
export const houseForSign = (signIndex: number, ascIndex: number): number =>
  ((signIndex - ascIndex + 12) % 12) + 1;

/** Sign index occupying a given house. */
export const signForHouse = (house: number, ascIndex: number): number =>
  (ascIndex + house - 1) % 12;
