import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatPercent(val: number): string {
  return `${Math.round(val * 100)}%`;
}

export function truncateText(text: string, len: number): string {
  if (!text) return "";
  if (text.length <= len) return text;
  return text.slice(0, len) + "...";
}
