"use client";

import React, { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard, 
  MessageSquare, 
  BarChart3, 
  FileText, 
  Link2, 
  Settings, 
  Volume2, 
  Cpu, 
  Palette, 
  Users,
  ChevronLeft,
  ChevronRight,
  LogOut,
  Sparkles,
  Trophy,
  BellRing,
  Activity,
  Shield,
  KeyRound,
  Webhook,
  LayoutGrid,
  Navigation,
  QrCode,
  Search,
  Network,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useAuthStore } from "@/stores/auth-store";
import { useBrandingStore } from "@/stores/branding-store";
import { ROUTES } from "@/lib/constants";

export default function Sidebar() {
  const pathname = usePathname();
  const logout = useAuthStore((state) => state.logout);
  const user = useAuthStore((state) => state.user);
  const config = useBrandingStore((state) => state.brandingConfig);
  
  const [isCollapsed, setIsCollapsed] = useState(false);
  const [showSettingsSub, setShowSettingsSub] = useState(true);

  const brandName = config?.company_name || "ReputationOS AI";

  const mainNav = [
    { label: "Dashboard", href: ROUTES.DASHBOARD, icon: LayoutDashboard },
    { label: "Copilot", href: ROUTES.COPILOT, icon: Sparkles },
    { label: "Reviews", href: ROUTES.REVIEWS, icon: MessageSquare },
    { label: "Analytics", href: ROUTES.ANALYTICS, icon: BarChart3 },
    { label: "Dashboards", href: "/dashboard/custom-dashboards", icon: LayoutGrid },
    { label: "Competitors", href: ROUTES.COMPETITORS, icon: Trophy },
    { label: "Alerts", href: ROUTES.ALERTS, icon: BellRing },
    { label: "Reports", href: ROUTES.REPORTS, icon: FileText },
    { label: "Integrations", href: ROUTES.INTEGRATIONS, icon: Link2 },
    { label: "Review Campaigns", href: ROUTES.REVIEW_CAMPAIGNS, icon: QrCode },
    { label: "Local SEO", href: ROUTES.SEO, icon: Search },
    { label: "Customer Journey", href: "/dashboard/customer-journey", icon: Navigation },
  ];

  const settingsNav = [
    { label: "Brand Voice", href: ROUTES.BRAND_VOICE, icon: Volume2 },
    { label: "Smart Rules", href: ROUTES.SMART_RULES, icon: Cpu },
    { label: "Branding", href: ROUTES.BRANDING, icon: Palette },
    { label: "Team", href: ROUTES.TEAM, icon: Users },
    { label: "API & Integrations", href: "/dashboard/settings/integrations", icon: Network },
    { label: "Audit Logs", href: ROUTES.AUDIT_LOGS || "/dashboard/settings/audit-logs", icon: Activity },
    { label: "Security", href: "/dashboard/settings/security", icon: Shield },
    { label: "API Keys", href: "/dashboard/settings/api-keys", icon: KeyRound },
    { label: "Webhooks", href: "/dashboard/settings/webhooks", icon: Webhook },
  ];

  const handleLogout = () => {
    logout();
    window.location.href = ROUTES.LOGIN;
  };

  return (
    <div 
      className={cn(
        "bg-background border-r border-border min-h-screen flex flex-col transition-all duration-300 relative z-30 select-none",
        isCollapsed ? "w-16" : "w-64"
      )}
    >
      {/* Logo Area */}
      <div className="h-16 flex items-center justify-between px-4 border-b border-border">
        {!isCollapsed && (
          <div className="flex items-center gap-2 font-bold text-lg text-foreground tracking-tight">
            <span className="w-6 h-6 rounded bg-primary flex items-center justify-center text-primary-foreground font-black text-xs">
              R
            </span>
            {brandName}
          </div>
        )}
        {isCollapsed && (
          <span className="w-8 h-8 rounded bg-primary flex items-center justify-center text-primary-foreground font-black text-sm mx-auto">
            R
          </span>
        )}
      </div>

      {/* Nav List */}
      <div className="flex-1 py-4 flex flex-col gap-1.5 overflow-y-auto px-3">
        {mainNav.map((item) => {
          const isActive = pathname === item.href;
          const Icon = item.icon;
          
          return (
            <Link 
              key={item.href} 
              href={item.href}
              className={cn(
                "flex items-center gap-3 px-3 py-2.5 rounded-md text-sm transition-all duration-200 cursor-pointer group",
                isActive 
                  ? "bg-accent text-accent-foreground font-medium" 
                  : "text-muted-foreground hover:text-foreground hover:bg-accent/50"
              )}
            >
              <Icon className={cn("w-5 h-5 shrink-0 transition-colors", isActive ? "text-foreground" : "text-muted-foreground group-hover:text-foreground")} />
              {!isCollapsed && <span>{item.label}</span>}
            </Link>
          );
        })}

        {/* Settings Sub-heading */}
        <div className="mt-4">
          <button 
            onClick={() => !isCollapsed && setShowSettingsSub(!showSettingsSub)}
            className={cn(
              "w-full flex items-center justify-between text-muted-foreground font-medium uppercase tracking-wider text-[10px] px-3 mb-1 hover:text-foreground transition-colors cursor-pointer",
              isCollapsed && "justify-center"
            )}
          >
            {isCollapsed ? <Settings className="w-4 h-4 text-muted-foreground" /> : <span>Settings</span>}
          </button>
          
          {(!isCollapsed && showSettingsSub) && (
            <div className="flex flex-col gap-1 pl-2">
              {settingsNav.map((sub) => {
                const isSubActive = pathname === sub.href;
                const SubIcon = sub.icon;
                
                return (
                  <Link 
                    key={sub.href} 
                    href={sub.href}
                    className={cn(
                      "flex items-center gap-3 px-3 py-2 rounded-md text-xs transition-all duration-200 cursor-pointer group",
                      isSubActive 
                        ? "bg-accent text-accent-foreground font-medium" 
                        : "text-muted-foreground hover:text-foreground hover:bg-accent/50"
                    )}
                  >
                    <SubIcon className={cn("w-4 h-4 shrink-0 transition-colors", isSubActive ? "text-foreground" : "text-muted-foreground group-hover:text-foreground")} />
                    <span>{sub.label}</span>
                  </Link>
                );
              })}
            </div>
          )}
        </div>
      </div>

      {/* User Panel */}
      <div className="p-3 border-t border-border flex flex-col gap-2">
        {!isCollapsed && (
          <div className="flex items-center gap-3 px-2 py-1.5 rounded-md border border-border bg-card">
            <div className="w-8 h-8 rounded bg-secondary flex items-center justify-center text-secondary-foreground font-bold text-xs">
              {user?.name?.slice(0, 2).toUpperCase() || "US"}
            </div>
            <div className="flex-1 overflow-hidden">
              <div className="text-xs font-medium text-foreground truncate">{user?.name}</div>
              <div className="text-[10px] text-muted-foreground truncate uppercase tracking-wider">{user?.role?.replace("_", " ")}</div>
            </div>
          </div>
        )}
        
        <button 
          onClick={handleLogout}
          className={cn(
            "w-full flex items-center gap-3 px-3 py-2 rounded-md text-xs font-medium text-muted-foreground hover:text-foreground hover:bg-accent transition-all duration-200 cursor-pointer",
            isCollapsed && "justify-center"
          )}
        >
          <LogOut className="w-4 h-4 shrink-0" />
          {!isCollapsed && <span>Logout Session</span>}
        </button>
      </div>

      {/* Collapse Trigger Button */}
      <button 
        onClick={() => setIsCollapsed(!isCollapsed)}
        className="absolute top-1/2 -right-3 transform -translate-y-1/2 w-6 h-6 rounded-full bg-background border border-border flex items-center justify-center text-muted-foreground hover:text-foreground shadow-sm cursor-pointer hover:scale-105 transition-all"
      >
        {isCollapsed ? <ChevronRight className="w-3.5 h-3.5" /> : <ChevronLeft className="w-3.5 h-3.5" />}
      </button>
    </div>
  );
}
