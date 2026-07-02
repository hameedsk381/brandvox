import { create } from "zustand";
import { Client, Location } from "@/types";

interface TenantState {
  currentClient: Client | null;
  currentLocation: Location | null;
  clients: Client[];
  locations: Location[];
  setClients: (clients: Client[]) => void;
  setLocations: (locations: Location[]) => void;
  setClient: (client: Client | null) => void;
  setLocation: (location: Location | null) => void;
}

export const useTenantStore = create<TenantState>((set) => ({
  currentClient: null,
  currentLocation: null,
  clients: [],
  locations: [],
  setClients: (clients) => set({ clients }),
  setLocations: (locations) => set({ locations }),
  setClient: (client) => set({ currentClient: client }),
  setLocation: (location) => set({ currentLocation: location }),
}));
