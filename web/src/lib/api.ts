import {
  SUPPORTED_CONTRACT,
  type BirthInput,
  type ChartResponse,
  type CompatibilityResponse,
  type PersonInput,
} from "@/types/chart";

/**
 * The only network call this app makes.
 *
 * Same-origin in every environment: Next rewrites /api/* to the Python engine
 * in development, and in production both sit behind one host. Nothing is sent
 * anywhere else, which is the whole privacy posture of the project restated at
 * the client boundary.
 */
export async function fetchChart(input: BirthInput): Promise<ChartResponse> {
  const body = new URLSearchParams({
    name: input.name,
    birth_date: input.birth_date,
    birth_time: input.birth_time,
    city: input.city,
  });

  const res = await fetch("/api/chart", {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body,
    cache: "no-store",
  });

  if (!res.ok) {
    let detail = `The engine returned ${res.status}.`;
    try {
      const parsed = (await res.json()) as { detail?: string };
      if (parsed.detail) detail = parsed.detail;
    } catch {
      /* a non-JSON error body is not worth surfacing verbatim */
    }
    throw new Error(detail);
  }

  const data = (await res.json()) as ChartResponse;

  // Fail loudly on a contract mismatch. A frontend quietly rendering fields
  // that changed meaning is exactly the class of error this project exists to
  // avoid, so it is better to refuse than to draw something plausible.
  const [major] = data.contract_version.split(".");
  const [supportedMajor] = SUPPORTED_CONTRACT.split(".");
  if (major !== supportedMajor) {
    throw new Error(
      `This client speaks contract ${SUPPORTED_CONTRACT} but the engine sent ` +
        `${data.contract_version}. Refusing to render rather than guess.`,
    );
  }

  return data;
}

/** Julian Day to a readable date, for timeline scrubbing. */
export function jdToDate(jd: number): Date {
  return new Date((jd - 2440587.5) * 86400000);
}

export function formatYear(jd: number): string {
  return String(jdToDate(jd).getUTCFullYear());
}

/** Pairwise compatibility across two or three charts. */
export async function fetchCompatibility(
  people: PersonInput[],
  mode: "relationship" | "friendship",
): Promise<CompatibilityResponse> {
  const body = new URLSearchParams({ mode, include_third: people.length > 2 ? "yes" : "no" });
  people.slice(0, 3).forEach((p, i) => {
    const tag = ["a", "b", "c"][i] as string;
    body.set(`${tag}_name`, p.name);
    body.set(`${tag}_date`, p.birth_date);
    body.set(`${tag}_time`, p.birth_time);
    body.set(`${tag}_city`, p.city);
  });

  const res = await fetch("/api/compatibility", {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body,
    cache: "no-store",
  });

  if (!res.ok) {
    let detail = `The engine returned ${res.status}.`;
    try {
      const parsed = (await res.json()) as { detail?: string };
      if (parsed.detail) detail = parsed.detail;
    } catch {
      /* a non-JSON error body is not worth surfacing verbatim */
    }
    throw new Error(detail);
  }

  const data = (await res.json()) as CompatibilityResponse;
  const [major] = data.contract_version.split(".");
  const [supportedMajor] = SUPPORTED_CONTRACT.split(".");
  if (major !== supportedMajor) {
    throw new Error(
      `This client speaks contract ${SUPPORTED_CONTRACT} but the engine sent ` +
        `${data.contract_version}. Refusing to render rather than guess.`,
    );
  }
  return data;
}
