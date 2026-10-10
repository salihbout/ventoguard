const n0 = new Intl.NumberFormat("en-GB", { maximumFractionDigits: 0 });

export function eur(x: number | null | undefined): string {
  const v = Number(x ?? 0);
  if (Math.abs(v) >= 1e6) return `€${(v / 1e6).toFixed(2)} M`;
  if (Math.abs(v) >= 1e3) return `€${n0.format(v / 1e3)} k`;
  return `€${n0.format(v)}`;
}
export const pct = (x: number | null | undefined, digits = 1) => `${(Number(x ?? 0) * 100).toFixed(digits)} %`;
export const num = (x: number | null | undefined) => n0.format(Number(x ?? 0));
export const component = (c: string) => c.replace(/_/g, " ");
export const farmLabel = (f: string) => f.replace("Kueste", "Küste").replace("Hunsrueck Hoehe", "Hunsrück Höhe");
