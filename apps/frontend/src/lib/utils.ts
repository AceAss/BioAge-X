import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatPValue(p: number): string {
  if (p < 0.0001) {
    return p.toExponential(2);
  }
  return p.toFixed(4);
}

export function formatYears(years: number): string {
  const prefix = years > 0 ? "+" : "";
  return `${prefix}${years.toFixed(1)} yrs`;
}
