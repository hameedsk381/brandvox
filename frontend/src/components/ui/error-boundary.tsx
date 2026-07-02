"use client";

import React, { Component, ErrorInfo, ReactNode } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { AlertTriangle } from "lucide-react";

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export default class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo): void {
    console.error("ErrorBoundary caught an error:", error, errorInfo);
  }

  handleReset = (): void => {
    this.setState({ hasError: false, error: null });
  };

  render(): ReactNode {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }

      return (
        <div className="flex items-center justify-center min-h-[400px] p-8">
          <Card className="max-w-md w-full border-rose-200">
            <CardHeader className="flex flex-col items-center text-center">
              <div className="w-12 h-12 rounded-full bg-rose-100 flex items-center justify-center mb-3">
                <AlertTriangle className="w-6 h-6 text-rose-500" />
              </div>
              <CardTitle className="text-lg">Something went wrong</CardTitle>
              <CardDescription className="text-sm text-muted-foreground mt-1">
                An unexpected error occurred. Please try again.
              </CardDescription>
            </CardHeader>
            <CardContent className="flex justify-center pb-6">
              <Button variant="outline" onClick={this.handleReset}>
                Try Again
              </Button>
            </CardContent>
          </Card>
        </div>
      );
    }

    return this.props.children;
  }
}
