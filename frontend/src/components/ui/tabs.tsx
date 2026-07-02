import React, { createContext, useContext, useState } from "react";
import { cn } from "@/lib/utils";

interface TabsContextType {
  activeTab: string;
  setActiveTab: (value: string) => void;
}

const TabsContext = createContext<TabsContextType | undefined>(undefined);

export interface TabsProps extends React.HTMLAttributes<HTMLDivElement> {
  defaultValue: string;
  children: React.ReactNode;
}

export const Tabs = ({ defaultValue, children, className, ...props }: TabsProps) => {
  const [activeTab, setActiveTab] = useState(defaultValue);
  
  return (
    <TabsContext.Provider value={{ activeTab, setActiveTab }}>
      <div className={cn("w-full", className)} {...props}>
        {children}
      </div>
    </TabsContext.Provider>
  );
};

export const TabsList = ({ children, className, ...props }: React.HTMLAttributes<HTMLDivElement>) => (
  <div 
    className={cn("inline-flex h-10 items-center justify-center rounded-lg bg-muted p-1 text-muted-foreground gap-1", className)}
    {...props}
  >
    {children}
  </div>
);

export interface TabsTriggerProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  value: string;
}

export const TabsTrigger = ({ value, children, className, ...props }: TabsTriggerProps) => {
  const context = useContext(TabsContext);
  if (!context) throw new Error("TabsTrigger must be used inside Tabs");
  
  const isActive = context.activeTab === value;
  
  return (
    <button
      onClick={() => context.setActiveTab(value)}
      className={cn(
        "inline-flex items-center justify-center whitespace-nowrap rounded-md px-3 py-1.5 text-sm font-medium transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 cursor-pointer",
        isActive 
          ? "bg-background text-foreground shadow-sm" 
          : "hover:bg-background/50 hover:text-foreground",
        className
      )}
      {...props}
    >
      {children}
    </button>
  );
};

export interface TabsContentProps extends React.HTMLAttributes<HTMLDivElement> {
  value: string;
}

export const TabsContent = ({ value, children, className, ...props }: TabsContentProps) => {
  const context = useContext(TabsContext);
  if (!context) throw new Error("TabsContent must be used inside Tabs");
  
  if (context.activeTab !== value) return null;
  
  return (
    <div className={cn("mt-4 outline-none", className)} {...props}>
      {children}
    </div>
  );
};
