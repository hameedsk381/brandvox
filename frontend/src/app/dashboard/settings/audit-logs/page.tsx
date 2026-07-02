"use client";

import { useState, useEffect } from "react";
import { auditAPI } from "@/lib/api";
import { Loader2, Activity, User, Search, Filter } from "lucide-react";
import toast from "react-hot-toast";
import { format } from "date-fns";

export default function AuditLogsPage() {
  const [logs, setLogs] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [filterAction, setFilterAction] = useState("");
  const [filterResource, setFilterResource] = useState("");

  const fetchLogs = async () => {
    try {
      setIsLoading(true);
      const data = await auditAPI.list({
        action: filterAction || undefined,
        resource_type: filterResource || undefined,
        limit: 100
      });
      setLogs(data);
    } catch (error: any) {
      toast.error(error.message || "Failed to fetch audit logs");
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchLogs();
  }, [filterAction, filterResource]);

  const uniqueActions = Array.from(new Set(logs.map(l => l.action))).filter(Boolean);
  const uniqueResources = Array.from(new Set(logs.map(l => l.resource_type))).filter(Boolean);

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-foreground flex items-center">
            <Activity className="w-6 h-6 mr-2 text-primary" />
            Audit Logs
          </h1>
          <p className="text-muted-foreground mt-1">
            Track actions and events across your agency.
          </p>
        </div>
      </div>

      <div className="bg-card border border-border rounded-xl shadow-sm overflow-hidden">
        {/* Filters */}
        <div className="p-4 border-b border-border bg-muted/20 flex gap-4">
          <div className="flex items-center gap-2">
            <Filter className="w-4 h-4 text-muted-foreground" />
            <select
              className="text-sm bg-background border border-border rounded px-3 py-1.5 focus:ring-1 focus:ring-primary outline-none"
              value={filterAction}
              onChange={(e) => setFilterAction(e.target.value)}
            >
              <option value="">All Actions</option>
              {uniqueActions.map((a: string) => (
                <option key={a} value={a}>{a}</option>
              ))}
            </select>
          </div>
          <div className="flex items-center gap-2">
            <select
              className="text-sm bg-background border border-border rounded px-3 py-1.5 focus:ring-1 focus:ring-primary outline-none"
              value={filterResource}
              onChange={(e) => setFilterResource(e.target.value)}
            >
              <option value="">All Resources</option>
              {uniqueResources.map((r: string) => (
                <option key={r} value={r}>{r}</option>
              ))}
            </select>
          </div>
        </div>

        {/* Table */}
        <div className="overflow-x-auto">
          <table className="w-full text-sm text-left">
            <thead className="text-xs text-muted-foreground uppercase bg-muted/50 border-b border-border">
              <tr>
                <th className="px-6 py-3">Timestamp</th>
                <th className="px-6 py-3">Action</th>
                <th className="px-6 py-3">User</th>
                <th className="px-6 py-3">Resource</th>
                <th className="px-6 py-3">Details</th>
              </tr>
            </thead>
            <tbody>
              {isLoading ? (
                <tr>
                  <td colSpan={5} className="px-6 py-8 text-center">
                    <Loader2 className="w-6 h-6 animate-spin mx-auto text-primary" />
                  </td>
                </tr>
              ) : logs.length === 0 ? (
                <tr>
                  <td colSpan={5} className="px-6 py-8 text-center text-muted-foreground">
                    No audit logs found matching criteria.
                  </td>
                </tr>
              ) : (
                logs.map((log) => (
                  <tr key={log.id} className="border-b border-border hover:bg-muted/30">
                    <td className="px-6 py-4 whitespace-nowrap text-muted-foreground">
                      {format(new Date(log.created_at), "MMM d, yyyy HH:mm:ss")}
                    </td>
                    <td className="px-6 py-4">
                      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-primary/10 text-primary">
                        {log.action}
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      {log.user_name ? (
                        <div className="flex items-center">
                          <User className="w-3 h-3 mr-1.5 text-muted-foreground" />
                          <span title={log.user_email}>{log.user_name}</span>
                        </div>
                      ) : (
                        <span className="text-muted-foreground italic">System</span>
                      )}
                    </td>
                    <td className="px-6 py-4 text-muted-foreground">
                      {log.resource_type} {log.resource_id && <span className="text-xs opacity-70 ml-1">({log.resource_id.slice(0, 8)}...)</span>}
                    </td>
                    <td className="px-6 py-4">
                      <pre className="text-xs bg-muted/50 p-2 rounded border border-border overflow-x-auto max-w-xs">
                        {JSON.stringify(log.details, null, 2)}
                      </pre>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
