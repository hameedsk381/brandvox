"use client";

import React, { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useTenantStore } from "@/stores/tenant-store";
import { useAuthStore } from "@/stores/auth-store";
import { alertsAPI } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { 
  BellRing, 
  AlertTriangle, 
  CheckCircle, 
  ShieldAlert, 
  Trash2, 
  Link2,
  Slack,
  Mail,
  MessageSquare
} from "lucide-react";
import toast from "react-hot-toast";

export default function AlertsPage() {
  const queryClient = useQueryClient();
  const currentLocation = useTenantStore((state) => state.currentLocation);
  const user = useAuthStore((state) => state.user);

  // Integrations state
  const [slackUrl, setSlackUrl] = useState("");
  const [teamsUrl, setTeamsUrl] = useState("");

  const { data: alerts, isLoading: isLoadingAlerts } = useQuery({
    queryKey: ["alerts", currentLocation?.id],
    queryFn: () => alertsAPI.list(currentLocation!.id),
    enabled: !!currentLocation?.id,
  });

  const { data: integrations, isLoading: isLoadingIntegrations } = useQuery({
    queryKey: ["alert-integrations", currentLocation?.id],
    queryFn: () => alertsAPI.getIntegrations(currentLocation!.id),
    enabled: !!currentLocation?.id,
  });

  // Pre-fill inputs when integrations load
  React.useEffect(() => {
    if (integrations) {
      const slack = integrations.find((i: any) => i.type === "slack");
      const teams = integrations.find((i: any) => i.type === "teams");
      if (slack) setSlackUrl(slack.webhook_url);
      if (teams) setTeamsUrl(teams.webhook_url);
    }
  }, [integrations]);

  const resolveMutation = useMutation({
    mutationFn: (alertId: string) => alertsAPI.resolve(currentLocation!.id, alertId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["alerts"] });
      toast.success("Alert marked as resolved");
    },
    onError: () => toast.error("Failed to resolve alert"),
  });

  const upsertIntegrationMutation = useMutation({
    mutationFn: ({ type, url }: { type: string, url: string }) => 
      alertsAPI.upsertIntegration(currentLocation!.id, type, url, true),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["alert-integrations"] });
      toast.success("Integration updated successfully");
    },
    onError: () => toast.error("Failed to update integration"),
  });

  const handleSaveSlack = () => {
    if (!slackUrl.trim()) return;
    upsertIntegrationMutation.mutate({ type: "slack", url: slackUrl });
  };

  const handleSaveTeams = () => {
    if (!teamsUrl.trim()) return;
    upsertIntegrationMutation.mutate({ type: "teams", url: teamsUrl });
  };

  if (!currentLocation) {
    return (
      <div className="flex flex-col items-center justify-center h-96 text-muted-foreground">
        <BellRing className="w-16 h-16 opacity-20 mb-4" />
        <h3 className="text-lg font-medium text-foreground">Select a location</h3>
        <p className="text-sm">Please select a business location to view alerts.</p>
      </div>
    );
  }

  const getSeverityBadge = (severity: string) => {
    switch (severity) {
      case "critical": return <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-rose-500/20 text-rose-400 border border-rose-500/30 uppercase tracking-wider">Critical</span>;
      case "high": return <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-amber-500/20 text-amber-400 border border-amber-500/30 uppercase tracking-wider">High</span>;
      default: return <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-yellow-500/20 text-yellow-400 border border-yellow-500/30 uppercase tracking-wider">Medium</span>;
    }
  };

  const getCategoryIcon = (category: string) => {
    switch (category) {
      case "health_safety": return <ShieldAlert className="w-4 h-4 text-rose-500" />;
      case "legal": return <AlertTriangle className="w-4 h-4 text-amber-500" />;
      default: return <BellRing className="w-4 h-4 text-primary" />;
    }
  };

  return (
    <div className="max-w-5xl mx-auto flex flex-col gap-6">
      <div className="flex flex-col gap-1">
        <h1 className="text-2xl font-bold text-foreground">Crisis Center & Alerts</h1>
        <p className="text-sm text-muted-foreground">Monitor and configure PR crisis and safety alerts for {currentLocation.name}</p>
      </div>

      <Tabs defaultValue="alerts" className="w-full">
        <TabsList className="mb-4">
          <TabsTrigger value="alerts">Active Alerts</TabsTrigger>
          <TabsTrigger value="integrations">Webhooks & Integrations</TabsTrigger>
        </TabsList>

        <TabsContent value="alerts" className="flex flex-col gap-4">
          {isLoadingAlerts ? (
            <div className="text-center py-12 text-muted-foreground">Loading alerts...</div>
          ) : !alerts || alerts.length === 0 ? (
            <Card className="border-dashed border-border bg-transparent">
              <CardContent className="flex flex-col items-center justify-center py-12 text-muted-foreground">
                <CheckCircle className="w-12 h-12 opacity-20 mb-3" />
                <p>No crisis alerts detected.</p>
                <p className="text-xs mt-1">All quiet on the front.</p>
              </CardContent>
            </Card>
          ) : (
            alerts.map((alert: any) => (
              <Card key={alert.id} className={`border-l-4 ${alert.status === 'resolved' ? 'border-l-muted opacity-60' : alert.severity === 'critical' ? 'border-l-rose-500' : 'border-l-amber-500'}`}>
                <CardContent className="p-5 flex flex-col md:flex-row gap-4 items-start md:items-center justify-between">
                  <div className="flex flex-col gap-2">
                    <div className="flex items-center gap-2">
                      {getCategoryIcon(alert.category)}
                      <span className="text-sm font-bold uppercase tracking-wider">{alert.category.replace("_", " ")}</span>
                      {getSeverityBadge(alert.severity)}
                      {alert.status === "resolved" && (
                        <span className="text-xs px-2 py-0.5 rounded-full bg-muted text-muted-foreground ml-2">Resolved</span>
                      )}
                    </div>
                    <div className="text-sm font-medium">"{alert.review_text}"</div>
                    <div className="text-xs text-muted-foreground">
                      Review by <span className="font-semibold">{alert.author_name}</span> &bull; {alert.rating} Stars &bull; AI Diagnosis: {alert.analysis_reason}
                    </div>
                  </div>
                  
                  {alert.status === 'open' && (
                    <Button size="sm" variant="outline" onClick={() => resolveMutation.mutate(alert.id)} loading={resolveMutation.isPending}>
                      <CheckCircle className="w-4 h-4 mr-2" /> Mark Resolved
                    </Button>
                  )}
                </CardContent>
              </Card>
            ))
          )}
        </TabsContent>

        <TabsContent value="integrations" className="flex flex-col gap-6">
          <Card className="border-border">
            <CardHeader>
              <CardTitle className="text-base flex items-center gap-2">
                <Slack className="w-5 h-5 text-indigo-400" /> Slack Webhook
              </CardTitle>
              <CardDescription>Receive crisis alerts directly in a Slack channel.</CardDescription>
            </CardHeader>
            <CardContent className="flex flex-col gap-4">
              <div className="flex gap-3">
                <Input 
                  placeholder="https://hooks.slack.com/services/..." 
                  value={slackUrl}
                  onChange={(e) => setSlackUrl(e.target.value)}
                  className="flex-1"
                />
                <Button onClick={handleSaveSlack} loading={upsertIntegrationMutation.isPending}>Save</Button>
              </div>
            </CardContent>
          </Card>

          <Card className="border-border">
            <CardHeader>
              <CardTitle className="text-base flex items-center gap-2">
                <MessageSquare className="w-5 h-5 text-blue-500" /> Microsoft Teams
              </CardTitle>
              <CardDescription>Receive crisis alerts in Microsoft Teams using Incoming Webhooks.</CardDescription>
            </CardHeader>
            <CardContent className="flex flex-col gap-4">
              <div className="flex gap-3">
                <Input 
                  placeholder="https://...webhook.office.com/webhookb2/..." 
                  value={teamsUrl}
                  onChange={(e) => setTeamsUrl(e.target.value)}
                  className="flex-1"
                />
                <Button onClick={handleSaveTeams} loading={upsertIntegrationMutation.isPending}>Save</Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
