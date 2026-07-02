"use client";

import React, { useEffect, useState } from "react";
import { tenantAPI } from "@/lib/api";
import { useTenantStore } from "@/stores/tenant-store";
import { Client, Location } from "@/types";
import { Select } from "@/components/ui/select";
import { useAuthStore } from "@/stores/auth-store";

export default function TenantSwitcher() {
  const user = useAuthStore((state) => state.user);
  const { 
    currentClient, 
    currentLocation, 
    clients, 
    locations, 
    setClients, 
    setLocations, 
    setClient, 
    setLocation 
  } = useTenantStore();

  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadTenantData() {
      if (!user) return;
      try {
        setLoading(true);
        // Load clients & locations
        const clientsData = await tenantAPI.getClients();
        const locationsData = await tenantAPI.getLocations();
        
        setClients(clientsData);
        setLocations(locationsData);

        // Pre-select defaults
        if (clientsData.length > 0) {
          // If user has a scoped client, select that one. Otherwise select first.
          const defaultClient = user.client_id 
            ? clientsData.find((c: Client) => c.id === user.client_id)
            : clientsData[0];
          setClient(defaultClient || clientsData[0]);

          // Filter locations for selected client
          const clientLocs = locationsData.filter((l: Location) => l.client_id === (defaultClient?.id || clientsData[0].id));
          if (clientLocs.length > 0) {
            const defaultLoc = user.location_id
              ? clientLocs.find((l: Location) => l.id === user.location_id)
              : clientLocs[0];
            setLocation(defaultLoc || clientLocs[0]);
          }
        }
      } catch (e) {
        console.error("Error loading switcher data:", e);
      } finally {
        setLoading(false);
      }
    }

    loadTenantData();
  }, [user, setClients, setLocations, setClient, setLocation]);

  const handleClientChange = (clientId: string) => {
    const selected = clients.find((c) => c.id === clientId) || null;
    setClient(selected);
    
    // Auto-update locations list for this client
    if (selected) {
      const clientLocs = locations.filter((l) => l.client_id === selected.id);
      setLocation(clientLocs.length > 0 ? clientLocs[0] : null);
    } else {
      setLocation(null);
    }
  };

  const handleLocationChange = (locationId: string) => {
    const selected = locations.find((l) => l.id === locationId) || null;
    setLocation(selected);
  };

  if (loading) {
    return <div className="text-xs text-muted-foreground animate-pulse">Loading scopes...</div>;
  }

  // Filter locations for dropdown
  const activeLocations = currentClient 
    ? locations.filter((l) => l.client_id === currentClient.id) 
    : [];

  return (
    <div className="flex items-center gap-4">
      {/* Client Switcher (Visible to super_admin and agency_admin) */}
      {["super_admin", "agency_admin"].includes(user?.role || "") && clients.length > 0 && (
        <div className="w-48">
          <Select
            options={clients.map((c) => ({ value: c.id, label: c.name }))}
            value={currentClient?.id || ""}
            onChange={(e) => handleClientChange(e.target.value)}
            className="h-8 py-0 border-border/60 bg-background text-xs"
          />
        </div>
      )}
      
      {/* Client Display for Scoped Users */}
      {!["super_admin", "agency_admin"].includes(user?.role || "") && currentClient && (
        <span className="text-xs font-semibold px-2.5 py-1 rounded bg-muted border border-border text-muted-foreground">
          Client: {currentClient.name}
        </span>
      )}

      {/* Location Switcher */}
      {activeLocations.length > 0 && (
        <div className="w-48">
          <Select
            options={activeLocations.map((l) => ({ value: l.id, label: l.name }))}
            value={currentLocation?.id || ""}
            onChange={(e) => handleLocationChange(e.target.value)}
            className="h-8 py-0 border-border/60 bg-background text-xs"
            disabled={!!user?.location_id} // Lock for location scoped users
          />
        </div>
      )}
    </div>
  );
}
