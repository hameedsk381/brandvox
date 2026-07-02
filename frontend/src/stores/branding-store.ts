import { create } from "zustand";
import { BrandingConfig } from "@/types";

interface BrandingState {
  brandingConfig: BrandingConfig | null;
  setBranding: (config: BrandingConfig | null) => void;
  applyBranding: (config: BrandingConfig) => void;
}

// Convert Hex to RGB space-separated string (e.g. #6366f1 -> 99 102 241)
function hexToRgb(hex: string): string {
  // Strip hash
  const cleanHex = hex.replace("#", "");
  const num = parseInt(cleanHex, 16);
  const r = (num >> 16) & 255;
  const g = (num >> 8) & 255;
  const b = num & 255;
  return `${r} ${g} ${b}`;
}

export const useBrandingStore = create<BrandingState>((set) => ({
  brandingConfig: null,
  setBranding: (config) => {
    set({ brandingConfig: config });
    if (config) {
      // Automatically apply branding on store update
      const root = document.documentElement;
      
      // Update Tailwind CSS variables
      root.style.setProperty("--brand-primary", hexToRgb(config.primary_color));
      root.style.setProperty("--brand-secondary", hexToRgb(config.secondary_color));
      root.style.setProperty("--brand-accent", hexToRgb(config.accent_color));
      
      // Update non-color properties
      root.style.setProperty("--brand-font", config.font_family ? `'${config.font_family}', sans-serif` : "'Inter', sans-serif");
      root.style.setProperty("--brand-name", config.company_name || "ReputationOS AI");
    }
  },
  applyBranding: (config) => {
    const root = document.documentElement;
    root.style.setProperty("--brand-primary", hexToRgb(config.primary_color));
    root.style.setProperty("--brand-secondary", hexToRgb(config.secondary_color));
    root.style.setProperty("--brand-accent", hexToRgb(config.accent_color));
    root.style.setProperty("--brand-font", config.font_family ? `'${config.font_family}', sans-serif` : "'Inter', sans-serif");
    root.style.setProperty("--brand-name", config.company_name || "ReputationOS AI");
  }
}));
