"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { forecastingAPI } from "@/lib/api";
import { useTenantStore } from "@/stores/tenant-store";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { AnalyticsSkeleton } from "@/components/ui/page-skeleton";
import { 
  Brain, 
  TrendingUp, 
  TrendingDown, 
  AlertCircle, 
  Sparkles, 
  Calendar, 
  ShieldAlert, 
  CheckCircle,
  HelpCircle,
  Activity,
  Star
} from "lucide-react";
import { 
  LineChart, 
  Line, 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer, 
  Legend, 
  Cell 
} from "recharts";

export default function ForecastingPage() {
  const pathname = usePathname();
  const currentLocation = useTenantStore((state) => state.currentLocation);

  const { data: forecast, isLoading } = useQuery({
    queryKey: ["forecasting", currentLocation?.id],
    queryFn: () => forecastingAPI.get(currentLocation!.id),
    enabled: !!currentLocation?.id,
  });

  if (!currentLocation) {
    return (
      <div className="max-w-7xl mx-auto flex flex-col gap-6">
        <div>
          <h1 className="text-2xl font-bold text-foreground font-sans">Reputation Analytics</h1>
          <p className="text-sm text-muted-foreground mt-1">Select a location to view forecasting analytics.</p>
        </div>

        <Card className="border border-border bg-card">
          <CardContent className="h-64 flex flex-col items-center justify-center gap-4 text-center">
            <div className="w-12 h-12 rounded-full bg-zinc-800 flex items-center justify-center">
              <HelpCircle className="h-6 w-6 text-muted-foreground animate-pulse" />
            </div>
            <div className="flex flex-col gap-1 max-w-sm">
              <h3 className="font-semibold text-lg">No Location Selected</h3>
              <p className="text-sm text-muted-foreground">
                Please select a location from the switcher in the top bar to load the AI forecasting dashboard.
              </p>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="max-w-7xl mx-auto flex flex-col gap-6">
        <div className="flex flex-col gap-1">
          <h1 className="text-2xl font-bold text-foreground">AI Forecasting</h1>
          <p className="text-sm text-muted-foreground mt-1">{currentLocation.name}</p>
        </div>
        <AnalyticsSkeleton />
      </div>
    );
  }

  interface ChartDataPoint {
    name: string;
    rating: number;
    volume: number;
    isForecast: boolean;
  }

  // Combine historical data with upcoming predicted data for plotting
  const historical = forecast?.historical_data || [];
  const chartData: ChartDataPoint[] = historical.map((h: any) => ({
    name: h.month,
    rating: h.average_rating,
    volume: h.review_volume,
    isForecast: false,
  }));

  // Add the upcoming month's forecast point
  // Calculate next month label (e.g. current + 1 month)
  const getNextMonthLabel = () => {
    if (historical.length === 0) return "Next Month";
    const lastMonth = historical[historical.length - 1].month; // e.g., "Jun 2026"
    try {
      const parts = lastMonth.split(" ");
      if (parts.length === 2) {
        const monthNames = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
        const mIdx = monthNames.indexOf(parts[0]);
        let year = parseInt(parts[1]);
        if (mIdx !== -1) {
          const nextMIdx = (mIdx + 1) % 12;
          if (nextMIdx === 0) year += 1;
          return `${monthNames[nextMIdx]} ${year}`;
        }
      }
    } catch (e) {
      // Fallback
    }
    return "Forecast";
  };

  const nextMonthName = getNextMonthLabel();

  if (forecast) {
    chartData.push({
      name: `${nextMonthName} (FC)`,
      rating: forecast.predicted_rating,
      volume: forecast.predicted_volume,
      isForecast: true,
    });
  }

  // Assess churn risk severity class
  const getChurnRiskDetails = (score: number) => {
    if (score >= 70) return { label: "High Risk", color: "text-rose-400 bg-rose-500/10 border-rose-500/20", barColor: "bg-rose-500" };
    if (score >= 40) return { label: "Moderate Risk", color: "text-amber-400 bg-amber-500/10 border-amber-500/20", barColor: "bg-amber-500" };
    return { label: "Low Risk", color: "text-emerald-400 bg-emerald-500/10 border-emerald-500/20", barColor: "bg-emerald-500" };
  };

  const churnRisk = getChurnRiskDetails(forecast?.churn_risk_score || 0);

  return (
    <div className="max-w-7xl mx-auto flex flex-col gap-6">
      {/* Navigation tabs */}
      <div>
        <h1 className="text-2xl font-bold text-foreground">Analytics</h1>
        <p className="text-sm text-muted-foreground mt-1">{currentLocation.name}</p>
      </div>

      <div className="flex border-b border-border gap-6">
        <Link 
          href="/dashboard/analytics" 
          className={`pb-3 text-sm font-medium border-b-2 transition-all ${
            pathname === "/dashboard/analytics" 
              ? "border-primary text-primary" 
              : "border-transparent text-muted-foreground hover:text-foreground"
          }`}
        >
          Overview
        </Link>
        <Link 
          href="/dashboard/analytics/sentiment" 
          className={`pb-3 text-sm font-medium border-b-2 transition-all ${
            pathname === "/dashboard/analytics/sentiment" 
              ? "border-primary text-primary" 
              : "border-transparent text-muted-foreground hover:text-foreground"
          }`}
        >
          Sentiment Deep Dive
        </Link>
        <Link 
          href="/dashboard/analytics/forecasting" 
          className={`pb-3 text-sm font-medium border-b-2 transition-all ${
            pathname === "/dashboard/analytics/forecasting" 
              ? "border-primary text-primary" 
              : "border-transparent text-muted-foreground hover:text-foreground"
          }`}
        >
          AI Forecasting
        </Link>
      </div>

      {/* KPI Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Predicted Rating */}
        <Card className="relative overflow-hidden group hover:shadow-lg hover:shadow-indigo-500/5 transition-all duration-300 border-border bg-card">
          <div className="absolute top-0 left-0 right-0 h-[2px] bg-gradient-to-r from-indigo-500 via-purple-500 to-transparent" />
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Predicted Rating</CardTitle>
            <div className="w-8 h-8 rounded-lg bg-indigo-500/10 flex items-center justify-center">
              <Star className="h-4 w-4 text-indigo-400 fill-indigo-400" />
            </div>
          </CardHeader>
          <CardContent className="flex flex-col gap-2">
            <div className="flex items-baseline gap-2">
              <span className="text-3xl font-extrabold text-foreground tracking-tight">{forecast?.predicted_rating}</span>
              <span className="text-sm font-medium text-muted-foreground">/ 5.0</span>
            </div>
            <div className="flex items-center gap-1.5 text-xs text-muted-foreground mt-1">
              <Calendar className="h-3.5 w-3.5 text-zinc-500" />
              <span>Next month projection</span>
            </div>
          </CardContent>
        </Card>

        {/* Predicted Volume */}
        <Card className="relative overflow-hidden group hover:shadow-lg hover:shadow-pink-500/5 transition-all duration-300 border-border bg-card">
          <div className="absolute top-0 left-0 right-0 h-[2px] bg-gradient-to-r from-pink-500 via-rose-500 to-transparent" />
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Predicted Volume</CardTitle>
            <div className="w-8 h-8 rounded-lg bg-pink-500/10 flex items-center justify-center">
              <Activity className="h-4 w-4 text-pink-400" />
            </div>
          </CardHeader>
          <CardContent className="flex flex-col gap-2">
            <div className="flex items-baseline gap-2">
              <span className="text-3xl font-extrabold text-foreground tracking-tight">{forecast?.predicted_volume}</span>
              <span className="text-sm font-medium text-muted-foreground">Reviews</span>
            </div>
            <div className="flex items-center gap-1.5 text-xs text-muted-foreground mt-1">
              <Calendar className="h-3.5 w-3.5 text-zinc-500" />
              <span>Next month projection</span>
            </div>
          </CardContent>
        </Card>

        {/* Churn Risk */}
        <Card className="relative overflow-hidden group hover:shadow-lg hover:shadow-emerald-500/5 transition-all duration-300 border-border bg-card">
          <div className="absolute top-0 left-0 right-0 h-[2px] bg-gradient-to-r from-emerald-500 via-teal-500 to-transparent" />
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Churn Risk Score</CardTitle>
            <span className={`text-xs font-semibold px-2 py-0.5 rounded-full border ${churnRisk.color}`}>
              {churnRisk.label}
            </span>
          </CardHeader>
          <CardContent className="flex flex-col gap-3">
            <div className="flex items-baseline justify-between">
              <span className="text-3xl font-extrabold text-foreground tracking-tight">{forecast?.churn_risk_score}</span>
              <span className="text-xs font-medium text-muted-foreground">0 - 100 max</span>
            </div>
            {/* Custom progress bar */}
            <div className="w-full bg-zinc-800 rounded-full h-2">
              <div 
                className={`h-2 rounded-full transition-all duration-500 ${churnRisk.barColor}`} 
                style={{ width: `${forecast?.churn_risk_score || 0}%` }}
              />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Main Analytics Charts Section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Rating Trend Line Chart */}
        <Card className="border-border bg-card">
          <CardHeader>
            <CardTitle>Rating Projection Trend</CardTitle>
            <CardDescription>Historical monthly average ratings connected to next month's AI forecast</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="h-72">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#27272a" />
                  <XAxis dataKey="name" tick={{ fill: "#a1a1aa", fontSize: 11 }} tickLine={false} axisLine={false} />
                  <YAxis domain={[3.0, 5.0]} tick={{ fill: "#a1a1aa", fontSize: 11 }} tickLine={false} axisLine={false} />
                  <Tooltip
                    contentStyle={{ background: "#18181b", border: "1px solid #27272a", borderRadius: 8, color: "#f4f4f5" }}
                    formatter={(value: any, name: string) => [value, name === "rating" ? "Average Rating" : name]}
                  />
                  <Legend wrapperStyle={{ fontSize: 12, color: "#a1a1aa" }} />
                  <Line 
                    type="monotone" 
                    dataKey="rating" 
                    stroke="#6366f1" 
                    strokeWidth={2} 
                    dot={(props: any) => {
                      const { cx, cy, payload } = props;
                      const isFC = payload.isForecast;
                      return (
                        <circle 
                          key={payload.name} 
                          cx={cx} 
                          cy={cy} 
                          r={isFC ? 5 : 3.5} 
                          fill={isFC ? "#a855f7" : "#6366f1"} 
                          stroke={isFC ? "#ffffff" : "none"}
                          strokeWidth={isFC ? 1.5 : 0}
                        />
                      );
                    }}
                    name="Rating Trend" 
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>

        {/* Volume Trend Bar Chart */}
        <Card className="border-border bg-card">
          <CardHeader>
            <CardTitle>Review Volume Projection</CardTitle>
            <CardDescription>Monthly review counts showcasing the next month's expected volume</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="h-72">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#27272a" />
                  <XAxis dataKey="name" tick={{ fill: "#a1a1aa", fontSize: 11 }} tickLine={false} axisLine={false} />
                  <YAxis tick={{ fill: "#a1a1aa", fontSize: 11 }} tickLine={false} axisLine={false} />
                  <Tooltip
                    contentStyle={{ background: "#18181b", border: "1px solid #27272a", borderRadius: 8, color: "#f4f4f5" }}
                  />
                  <Legend wrapperStyle={{ fontSize: 12, color: "#a1a1aa" }} />
                  <Bar dataKey="volume" name="Review Volume" radius={[4, 4, 0, 0]}>
                    {chartData.map((entry, index) => (
                      <Cell 
                        key={`cell-${index}`} 
                        fill={entry.isForecast ? "#ec4899" : "#3b82f6"} 
                        fillOpacity={entry.isForecast ? 0.85 : 0.7}
                        stroke={entry.isForecast ? "#f43f5e" : "none"}
                        strokeWidth={entry.isForecast ? 1.5 : 0}
                      />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* AI Insights & Advice Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Reputation Risks Card */}
        <Card className="border-border bg-card">
          <CardHeader className="flex flex-row items-center gap-3">
            <div className="w-9 h-9 rounded-lg bg-rose-500/10 flex items-center justify-center">
              <ShieldAlert className="h-5 w-5 text-rose-400" />
            </div>
            <div>
              <CardTitle className="text-base">Predicted Risks</CardTitle>
              <CardDescription>Areas vulnerable to negative feedback</CardDescription>
            </div>
          </CardHeader>
          <CardContent>
            {forecast?.reputation_risks && forecast.reputation_risks.length > 0 ? (
              <ul className="flex flex-col gap-3">
                {forecast.reputation_risks.map((risk: string, i: number) => (
                  <li key={i} className="flex items-start gap-2.5 text-sm text-foreground">
                    <span className="w-1.5 h-1.5 rounded-full bg-rose-400 mt-2 shrink-0" />
                    <span>{risk}</span>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-sm text-muted-foreground flex items-center gap-2">
                <CheckCircle className="h-4 w-4 text-emerald-500" />
                No significant reputational risks detected.
              </p>
            )}
          </CardContent>
        </Card>

        {/* Seasonal Trends Card */}
        <Card className="border-border bg-card">
          <CardHeader className="flex flex-row items-center gap-3">
            <div className="w-9 h-9 rounded-lg bg-indigo-500/10 flex items-center justify-center">
              <Calendar className="h-5 w-5 text-indigo-400" />
            </div>
            <div>
              <CardTitle className="text-base">Seasonal Cycles & Trends</CardTitle>
              <CardDescription>Expected performance variations</CardDescription>
            </div>
          </CardHeader>
          <CardContent>
            {forecast?.seasonal_trends && forecast.seasonal_trends.length > 0 ? (
              <ul className="flex flex-col gap-3">
                {forecast.seasonal_trends.map((trend: string, i: number) => (
                  <li key={i} className="flex items-start gap-2.5 text-sm text-foreground">
                    <span className="w-1.5 h-1.5 rounded-full bg-indigo-400 mt-2 shrink-0" />
                    <span>{trend}</span>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-sm text-muted-foreground">No cyclical pattern changes forecasted.</p>
            )}
          </CardContent>
        </Card>

        {/* Actionable Advice Card */}
        <Card className="border-border bg-card relative overflow-hidden">
          <div className="absolute top-0 right-0 w-24 h-24 bg-gradient-to-br from-purple-500/10 to-pink-500/10 rounded-full blur-2xl pointer-events-none" />
          <CardHeader className="flex flex-row items-center gap-3">
            <div className="w-9 h-9 rounded-lg bg-purple-500/10 flex items-center justify-center">
              <Sparkles className="h-5 w-5 text-purple-400" />
            </div>
            <div>
              <CardTitle className="text-base">AI Strategic Advice</CardTitle>
              <CardDescription>Optimizations suggested by ReputationOS AI</CardDescription>
            </div>
          </CardHeader>
          <CardContent>
            <div className="bg-zinc-900/50 border border-zinc-800 rounded-lg p-3.5 flex flex-col gap-3">
              <div className="flex items-center gap-2">
                <Brain className="h-4 w-4 text-purple-400" />
                <span className="text-xs font-semibold text-purple-300 uppercase tracking-wider">AI Copilot Recommendation</span>
              </div>
              <p className="text-sm text-zinc-300 leading-relaxed">
                {forecast?.actionable_advice || "Continue monitoring trends and responding promptly to customer feedback."}
              </p>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
