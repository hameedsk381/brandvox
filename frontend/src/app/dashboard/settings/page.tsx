"use client";

import React from "react";
import Link from "next/link";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Volume2, Cpu, Palette, Users, ArrowRight, Network, Shield, KeyRound, Webhook } from "lucide-react";

const settingsLinks = [
  {
    label: "Brand Voice",
    href: "/dashboard/settings/brand-voice",
    icon: Volume2,
    desc: "Configure tone, vocabulary, and personality for AI replies",
  },
  {
    label: "Smart Rules",
    href: "/dashboard/settings/smart-rules",
    icon: Cpu,
    desc: "Define auto-reply rules based on ratings",
  },
  {
    label: "Branding",
    href: "/dashboard/settings/branding",
    icon: Palette,
    desc: "Customize logo, colors, and fonts for white-label",
  },
  {
    label: "Team",
    href: "/dashboard/settings/team",
    icon: Users,
    desc: "Manage users, roles, and permissions",
  },
  {
    label: "API & Integrations",
    href: "/dashboard/settings/integrations",
    icon: Network,
    desc: "Configure global API credentials (OAuth)",
  },
  {
    label: "Security",
    href: "/dashboard/settings/security",
    icon: Shield,
    desc: "Password, MFA, and data privacy controls",
  },
  {
    label: "API Keys",
    href: "/dashboard/settings/api-keys",
    icon: KeyRound,
    desc: "Manage keys for programmatic API access",
  },
  {
    label: "Webhooks",
    href: "/dashboard/settings/webhooks",
    icon: Webhook,
    desc: "Configure event-driven integrations",
  },
];

export default function SettingsPage() {
  return (
    <div className="max-w-4xl mx-auto flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-bold text-foreground">Settings</h1>
        <p className="text-sm text-muted-foreground mt-1">Manage your account and configuration</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {settingsLinks.map((item) => {
          const Icon = item.icon;
          return (
            <Link key={item.href} href={item.href}>
              <Card className="hover:border-border/60 transition-all h-full">
                <CardHeader>
                  <div className="flex items-center gap-2">
                    <Icon className="w-5 h-5 text-primary" />
                    <CardTitle className="text-sm">{item.label}</CardTitle>
                  </div>
                  <CardDescription>{item.desc}</CardDescription>
                </CardHeader>
                <CardContent>
                  <span className="text-xs text-primary flex items-center gap-1">
                    Configure <ArrowRight className="w-3 h-3" />
                  </span>
                </CardContent>
              </Card>
            </Link>
          );
        })}
      </div>
    </div>
  );
}
