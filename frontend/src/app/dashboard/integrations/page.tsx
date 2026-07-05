"use client";

import React, { useState, useEffect, useRef } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { useTenantStore } from "@/stores/tenant-store";
import { Building2, RefreshCw, CheckCircle2, AlertCircle, Bot } from "lucide-react";
import toast from "react-hot-toast";
import { useSearchParams, useRouter } from "next/navigation";
import Link from "next/link";
import { api, getErrorMessage, googleIntegrationsAPI } from "@/lib/api";
import { CustomerWidget } from "@/components/chat/customer-widget";

interface GoogleLocationOption {
  name: string;
  title: string;
}

interface GoogleIntegrationStatus {
  is_configured: boolean;
  is_connected: boolean;
  client_id?: string | null;
  google_account_id?: string | null;
  token_expires_at?: string | null;
  last_sync_status?: string | null;
  last_sync_error?: string | null;
  last_sync_attempt_at?: string | null;
  last_reply_status?: string | null;
  last_reply_error?: string | null;
  last_reply_attempt_at?: string | null;
  mapped_location_id?: string | null;
  mapped_google_location_id?: string | null;
  last_sync_time?: string | null;
  available_locations: GoogleLocationOption[];
  sync_failures?: number;
  next_sync_at?: string | null;
  google_api_error?: string | null;
}

export default function IntegrationsPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const currentClient = useTenantStore((state) => state.currentClient);
  const currentLocation = useTenantStore((state) => state.currentLocation);
  
  const [isConnecting, setIsConnecting] = useState(false);
  const [isConnected, setIsConnected] = useState(false);
  const [googleLocations, setGoogleLocations] = useState<GoogleLocationOption[]>([]);
  const [selectedGoogleLocation, setSelectedGoogleLocation] = useState("");
  const [isMapping, setIsMapping] = useState(false);
  const [isConfigured, setIsConfigured] = useState(true);
  const [isSyncing, setIsSyncing] = useState(false);
  const [status, setStatus] = useState<GoogleIntegrationStatus | null>(null);
  // OAuth codes are single-use; guard against React StrictMode double-firing
  // the effect and exchanging the same code twice.
  const callbackHandled = useRef(false);

  useEffect(() => {
    const code = searchParams.get("code");
    const state = searchParams.get("state");

    if (code && state) {
      if (!callbackHandled.current) {
        callbackHandled.current = true;
        handleOAuthCallback(code, state);
      }
      return;
    }

    if (currentClient) {
      refreshStatus(currentClient.id, currentLocation?.id);
    }
  }, [searchParams, currentClient?.id, currentLocation?.id]);

  useEffect(() => {
    if (status?.mapped_google_location_id) {
      setSelectedGoogleLocation(status.mapped_google_location_id);
    }
  }, [status?.mapped_google_location_id]);

  const refreshStatus = async (clientId: string, locationId?: string) => {
    try {
      const data = await googleIntegrationsAPI.getStatus(clientId, locationId);
      setStatus(data);
      setIsConfigured(data.is_configured);
      setIsConnected(data.is_connected);
      setGoogleLocations(data.available_locations || []);
    } catch (error) {
      toast.error(getErrorMessage(error, "Failed to load integration status"));
    }
  };

  const handleOAuthCallback = async (code: string, state: string) => {
    try {
      setIsConnecting(true);
      const res = await api.post(
        `/api/integrations/google/callback?code=${encodeURIComponent(code)}&state=${encodeURIComponent(state)}`
      );
      toast.success("Google account connected");
      router.replace("/dashboard/integrations");
      const clientId = res.data?.client_id || currentClient?.id;
      if (clientId) {
        await refreshStatus(clientId, currentLocation?.id);
      }
    } catch (error) {
      toast.error(getErrorMessage(error, "Failed to connect Google account"));
    } finally {
      setIsConnecting(false);
    }
  };

  const handleConnectGoogle = async () => {
    if (!currentClient) {
      toast.error("Please select a client first");
      return;
    }

    try {
      setIsConnecting(true);
      const data = await googleIntegrationsAPI.getAuthUrl(currentClient.id);
      window.location.href = data.url;
    } catch (error) {
      toast.error(getErrorMessage(error, "Failed to initiate connection"));
      setIsConnecting(false);
    }
  };

  const handleMapLocation = async () => {
    if (!currentLocation || !selectedGoogleLocation || !currentClient) return;

    try {
      setIsMapping(true);
      await googleIntegrationsAPI.mapLocation(currentLocation.id, selectedGoogleLocation);
      toast.success("Location mapped successfully");
      await refreshStatus(currentClient.id, currentLocation.id);
    } catch (error) {
      toast.error(getErrorMessage(error, "Failed to map location"));
    } finally {
      setIsMapping(false);
    }
  };

  const handleSync = async () => {
    if (!currentLocation || !currentClient) {
      toast.error("Please select a location first");
      return;
    }

    try {
      setIsSyncing(true);
      const result = await googleIntegrationsAPI.syncLocation(currentLocation.id);
      toast.success(`Sync completed: ${result.imported_reviews} imported, ${result.skipped_reviews} skipped`);
      await refreshStatus(currentClient.id, currentLocation.id);
    } catch (error) {
      toast.error(getErrorMessage(error, "Failed to sync reviews"));
    } finally {
      setIsSyncing(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-bold text-foreground">Integrations</h1>
        <p className="text-sm text-muted-foreground mt-1">Connect your data sources</p>
      </div>

      <Card className="bg-background/5 backdrop-blur-xl border-border dark:bg-[#0a0a0f]/50">
        <CardHeader>
          <div className="flex items-center gap-2">
            <Building2 className="w-5 h-5 text-primary" />
            <CardTitle>Google Business Profile</CardTitle>
          </div>
          <CardDescription>Connect your Google account to sync reviews automatically</CardDescription>
        </CardHeader>
        <CardContent className="flex flex-col gap-4">
          {!isConnected ? (
            <div className="flex flex-col gap-4">
              {!isConfigured && (
                <div className="p-4 rounded-lg bg-amber-500/10 border border-amber-500/20 text-amber-600 dark:text-amber-400 flex items-start gap-3">
                  <AlertCircle className="w-5 h-5 shrink-0 mt-0.5" />
                  <div className="flex flex-col gap-1">
                    <p className="font-medium text-sm">Google OAuth not configured</p>
                    <p className="text-xs">Your agency must add Google API credentials before clients can connect accounts.</p>
                    <Link href="/dashboard/settings/integrations" className="text-xs font-medium underline mt-1 w-fit hover:text-amber-500">
                      Go to integration settings
                    </Link>
                  </div>
                </div>
              )}

              <div className="flex items-center justify-between p-4 rounded-lg border border-border bg-muted/50 dark:bg-background/5">
                <div>
                  <h4 className="font-medium text-foreground">Connect account</h4>
                  <p className="text-sm text-muted-foreground">Authorize ReputationOS to read Google reviews for this client.</p>
                </div>
                <Button onClick={handleConnectGoogle} disabled={isConnecting || !currentClient || !isConfigured}>
                  {isConnecting ? <RefreshCw className="w-4 h-4 mr-2 animate-spin" /> : null}
                  Connect Google
                </Button>
              </div>
            </div>
          ) : (
            <div className="flex flex-col gap-3">
              <div className="flex items-center gap-2 p-4 rounded-lg border border-emerald-500/20 bg-emerald-500/10 text-emerald-500">
                <CheckCircle2 className="w-5 h-5" />
                <span className="font-medium">Google account connected</span>
              </div>
              <div className="grid gap-2 text-sm text-muted-foreground">
                <p>Selected client: {currentClient?.name || "None selected"}</p>
                <p>Connected account: {status?.google_account_id || "Connected"}</p>
                <p>Token expiry: {status?.token_expires_at ? new Date(status.token_expires_at).toLocaleString() : "Unknown"}</p>
                <p>Last sync: {status?.last_sync_time ? new Date(status.last_sync_time).toLocaleString() : "No sync has run yet"}</p>
                {status?.sync_failures != null && status.sync_failures > 0 && (
                  <p className="text-amber-400">Sync failures: {status.sync_failures} (exponential backoff active)</p>
                )}
                {status?.next_sync_at && (
                  <p>Next scheduled sync: {new Date(status.next_sync_at).toLocaleString()}</p>
                )}
              </div>

              {(status?.last_sync_status === "failed" || status?.last_reply_status === "failed") && (
                <div className="rounded-lg border border-rose-500/20 bg-rose-500/10 p-4 text-sm text-rose-300">
                  {status?.last_sync_status === "failed" && (
                    <p>
                      Sync failure
                      {status.last_sync_attempt_at ? ` at ${new Date(status.last_sync_attempt_at).toLocaleString()}` : ""}:
                      {" "}
                      {status.last_sync_error || "Unknown sync error"}
                    </p>
                  )}
                  {status?.last_reply_status === "failed" && (
                    <p>
                      Reply publish failure
                      {status.last_reply_attempt_at ? ` at ${new Date(status.last_reply_attempt_at).toLocaleString()}` : ""}:
                      {" "}
                      {status.last_reply_error || "Unknown reply error"}
                    </p>
                  )}
                </div>
              )}

              {status?.google_api_error && (
                <div className="rounded-lg border border-amber-500/20 bg-amber-500/10 p-4 text-sm text-amber-300">
                  <p>Google API error: {status.google_api_error}</p>
                </div>
              )}

              {(status?.last_sync_status === "success" || status?.last_reply_status === "success") && (
                <div className="rounded-lg border border-emerald-500/20 bg-emerald-500/10 p-4 text-sm text-emerald-300">
                  {status?.last_sync_status === "success" && (
                    <p>
                      Last sync attempt succeeded
                      {status.last_sync_attempt_at ? ` at ${new Date(status.last_sync_attempt_at).toLocaleString()}` : ""}.
                    </p>
                  )}
                  {status?.last_reply_status === "success" && (
                    <p>
                      Last Google reply publish succeeded
                      {status.last_reply_attempt_at ? ` at ${new Date(status.last_reply_attempt_at).toLocaleString()}` : ""}.
                    </p>
                  )}
                </div>
              )}
            </div>
          )}

          {isConnected && (
            <div className="mt-2 flex flex-col gap-4">
              <div>
                <h4 className="font-medium text-foreground mb-2">Map locations</h4>
                <p className="text-sm text-muted-foreground mb-4">
                  Map a Google location to your current internal location ({currentLocation?.name || "None selected"}).
                </p>

                <div className="flex gap-2">
                  <select
                    className="flex-1 h-10 rounded-md border border-border bg-transparent px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary/60"
                    value={selectedGoogleLocation}
                    onChange={(e) => setSelectedGoogleLocation(e.target.value)}
                  >
                    <option value="">Select Google location...</option>
                    {googleLocations.map((loc) => (
                      <option key={loc.name} value={loc.name}>
                        {loc.title} ({loc.name})
                      </option>
                    ))}
                  </select>
                  <Button onClick={handleMapLocation} disabled={isMapping || !selectedGoogleLocation || !currentLocation}>
                    {isMapping ? <RefreshCw className="w-4 h-4 mr-2 animate-spin" /> : null}
                    Save mapping
                  </Button>
                </div>
              </div>

              <div className="flex items-center justify-between p-4 rounded-lg border border-border bg-muted/40">
                <div>
                  <h4 className="font-medium text-foreground">Review sync</h4>
                  <p className="text-sm text-muted-foreground">
                    {status?.mapped_google_location_id
                      ? `Mapped to ${status.mapped_google_location_id}`
                      : "Map a Google location before syncing reviews."}
                  </p>
                </div>
                <Button onClick={handleSync} disabled={isSyncing || !status?.mapped_google_location_id || !currentLocation}>
                  {isSyncing ? <RefreshCw className="w-4 h-4 mr-2 animate-spin" /> : null}
                  Sync now
                </Button>
              </div>
            </div>
          )}

        </CardContent>
      </Card>

      <Card className="bg-background/5 backdrop-blur-xl border-border">
        <CardHeader>
          <div className="flex items-center gap-2">
            <Bot className="w-5 h-5 text-primary" />
            <CardTitle>AI Customer Chatbot Widget</CardTitle>
          </div>
          <CardDescription>
            Embed this AI widget on your public website to answer FAQs and intercept negative reviews.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="p-4 bg-muted/50 rounded-lg border border-border">
            <p className="text-sm text-foreground font-medium mb-2">Embed Code</p>
            <pre className="bg-background p-3 rounded border border-border text-xs text-muted-foreground overflow-x-auto">
            {`<!-- Add this right before your closing </body> tag -->
<script 
  src="${typeof window !== 'undefined' ? window.location.origin : 'https://reputationos.ai'}/widget.js" 
  data-client-id="${currentClient?.id || 'CLIENT_ID'}"
  data-brand-name="${currentClient?.name || 'Your Brand'}"
></script>`}
            </pre>
            <p className="text-xs text-muted-foreground mt-3">
              For testing purposes, the widget is actively loaded on this page in the bottom right corner.
            </p>
          </div>
        </CardContent>
      </Card>

      {currentClient && (
        <CustomerWidget
          clientId={currentClient.id}
          brandName={currentClient.name}
        />
      )}
    </div>
  );
}
