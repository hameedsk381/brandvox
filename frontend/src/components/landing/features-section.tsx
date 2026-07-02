"use client";

import React from "react";
import { Sparkles, BarChart3, Bot, Globe2, ShieldCheck, Zap } from "lucide-react";

const features = [
  {
    icon: Bot,
    title: "AI-Powered Replies",
    description: "Automatically generate personalized, context-aware responses to customer reviews in your unique brand voice."
  },
  {
    icon: Sparkles,
    title: "Sentiment Analysis",
    description: "Instantly understand the emotion behind every review with confidence scores and topic extraction."
  },
  {
    icon: BarChart3,
    title: "Actionable Analytics",
    description: "Track reputation scores, review velocity, and response rates across all your locations in real-time."
  },
  {
    icon: Globe2,
    title: "Multi-Location Scaling",
    description: "Manage thousands of locations or clients from a single, unified dashboard without breaking a sweat."
  },
  {
    icon: Zap,
    title: "Smart Automation Rules",
    description: "Set up trigger-based workflows to auto-reply to 5-star reviews and escalate 1-star reviews to management."
  },
  {
    icon: ShieldCheck,
    title: "White-Label Ready",
    description: "Customize the platform with your agency's colors, logo, and domain to offer reputation management as your own service."
  }
];

export default function FeaturesSection() {
  return (
    <section id="features" className="py-24 bg-background">
      <div className="max-w-7xl mx-auto px-6">
        <div className="text-center max-w-2xl mx-auto mb-16">
          <h2 className="text-3xl md:text-4xl font-bold tracking-tight text-foreground mb-4">
            Everything you need to dominate your local market
          </h2>
          <p className="text-muted-foreground text-lg">
            Powerful tools designed for agencies and multi-location brands to scale their reputation management effortlessly.
          </p>
        </div>
        
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
          {features.map((feature, idx) => {
            const Icon = feature.icon;
            return (
              <div key={idx} className="p-6 rounded-2xl border border-border bg-card hover:border-foreground/20 transition-colors">
                <div className="w-12 h-12 rounded-lg bg-accent flex items-center justify-center mb-6">
                  <Icon className="w-6 h-6 text-foreground" />
                </div>
                <h3 className="text-xl font-semibold text-foreground mb-3">{feature.title}</h3>
                <p className="text-muted-foreground leading-relaxed">
                  {feature.description}
                </p>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
