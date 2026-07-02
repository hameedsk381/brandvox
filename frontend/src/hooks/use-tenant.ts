"use client";

import { useQuery } from "@tanstack/react-query";
import { tenantAPI } from "@/lib/api";
import { useTenantStore } from "@/stores/tenant-store";
import { useAuthStore } from "@/stores/auth-store";
import { useEffect } from "react";

export function useClients() {
  const user = useAuthStore((state) => state.user);
  const setClients = useTenantStore((state) => state.setClients);
  const setClient = useTenantStore((state) => state.setClient);

  const query = useQuery({
    queryKey: ["clients"],
    queryFn: tenantAPI.getClients,
    enabled: !!user,
  });

  useEffect(() => {
    if (query.data) {
      setClients(query.data);
      if (!useTenantStore.getState().currentClient && query.data.length > 0) {
        const defaultClient = user?.client_id
          ? query.data.find((c: any) => c.id === user.client_id)
          : query.data[0];
        setClient(defaultClient || query.data[0]);
      }
    }
  }, [query.data, user, setClients, setClient]);

  return query;
}

export function useLocations() {
  const user = useAuthStore((state) => state.user);
  const setLocations = useTenantStore((state) => state.setLocations);
  const setLocation = useTenantStore((state) => state.setLocation);
  const currentClient = useTenantStore((state) => state.currentClient);

  const query = useQuery({
    queryKey: ["locations"],
    queryFn: tenantAPI.getLocations,
    enabled: !!user,
  });

  useEffect(() => {
    if (query.data) {
      setLocations(query.data);
      if (!useTenantStore.getState().currentLocation && currentClient) {
        const clientLocs = query.data.filter((l: any) => l.client_id === currentClient.id);
        if (clientLocs.length > 0) {
          const defaultLoc = user?.location_id
            ? clientLocs.find((l: any) => l.id === user.location_id)
            : clientLocs[0];
          setLocation(defaultLoc || clientLocs[0]);
        }
      }
    }
  }, [query.data, user, currentClient, setLocations, setLocation]);

  return query;
}
