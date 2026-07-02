import { create } from "zustand";
import { persist } from "zustand/middleware";

export interface SavedFilter {
  id: string;
  name: string;
  filters: Record<string, string | number | undefined>;
  createdAt: string;
}

interface FilterState {
  currentFilters: Record<string, string | number | undefined>;
  savedFilters: SavedFilter[];
  setCurrentFilters: (filters: Record<string, string | number | undefined>) => void;
  saveFilter: (name: string) => void;
  loadFilter: (id: string) => void;
  deleteFilter: (id: string) => void;
}

function generateId(): string {
  return Date.now().toString(36) + Math.random().toString(36).slice(2, 7);
}

export const useFilterStore = create<FilterState>()(
  persist(
    (set, get) => ({
      currentFilters: {},
      savedFilters: [],

      setCurrentFilters: (filters) => set({ currentFilters: filters }),

      saveFilter: (name) => {
        const { currentFilters, savedFilters } = get();
        const newFilter: SavedFilter = {
          id: generateId(),
          name,
          filters: { ...currentFilters },
          createdAt: new Date().toISOString(),
        };
        set({ savedFilters: [...savedFilters, newFilter] });
      },

      loadFilter: (id) => {
        const { savedFilters } = get();
        const found = savedFilters.find((f) => f.id === id);
        if (found) {
          set({ currentFilters: { ...found.filters } });
        }
      },

      deleteFilter: (id) => {
        const { savedFilters } = get();
        set({ savedFilters: savedFilters.filter((f) => f.id !== id) });
      },
    }),
    {
      name: "filter-storage",
    }
  )
);
