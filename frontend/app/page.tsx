"use client";

import { useState, useEffect } from "react";
import Dashboard from "@/components/Dashboard";
import ChatPanel from "@/components/ChatPanel";
import { LayoutDashboard, MessageCircle } from "lucide-react";

export interface DashboardData {
  metrics: {
    totalIncome: number;
    totalExpenses: number;
    netSavings: number;
    savingsRate: number;
    avgMonthly: number;
    transactionCount: number;
  };
  categories: { name: string; amount: number }[];
  monthlyTrends: Record<string, any>[];
  dailySpending: { date: string; amount: number }[];
  recentTransactions: {
    date: string;
    merchant: string;
    category: string;
    amount: number;
  }[];
  allTransactions: {
    date: string;
    merchant: string;
    category: string;
    amount: number;
  }[];
  profile: {
    name: string;
    monthly_income: number;
    current_savings: number;
    savings_goal: number;
    financial_goals: string[];
  };
  availableMonths: string[];
}

export default function Home() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [activeTab, setActiveTab] = useState<"dashboard" | "chat">("dashboard");
  const [loading, setLoading] = useState(true);

  const fetchData = () => {
    fetch("http://localhost:8003/api/dashboard")
      .then((res) => res.json())
      .then((d) => {
        setData(d);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  };

  useEffect(() => {
    fetchData();
  }, []);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[#0f1117]">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-indigo-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-slate-400">Loading your finances...</p>
        </div>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[#0f1117]">
        <div className="text-center max-w-md">
          <p className="text-xl font-semibold text-slate-200 mb-2">Cannot connect to FinMate API</p>
          <p className="text-slate-400">Make sure the backend is running on port 8000</p>
          <code className="mt-4 block bg-[#1e2235] rounded-lg p-3 text-sm text-slate-300 border border-[#2a2f45]">
            python -m uvicorn backend.api:app --port 8000
          </code>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#0f1117]">
      {/* Header */}
      <header className="sticky top-0 z-50 bg-[#0f1117]/80 backdrop-blur-md border-b border-[#2a2f45]">
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-xl flex items-center justify-center">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M12 2L2 7l10 5 10-5-10-5z"/>
                <path d="M2 17l10 5 10-5"/>
                <path d="M2 12l10 5 10-5"/>
              </svg>
            </div>
            <div>
              <h1 className="text-lg font-bold text-white">FinMate</h1>
              <p className="text-[10px] text-slate-500 -mt-0.5">AI Finance Assistant</p>
            </div>
          </div>

          {/* Tabs */}
          <nav className="flex gap-1 bg-[#1a1d2e] rounded-xl p-1">
            <button
              onClick={() => setActiveTab("dashboard")}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                activeTab === "dashboard"
                  ? "bg-[#2a2f45] text-white shadow-sm"
                  : "text-slate-400 hover:text-slate-200"
              }`}
            >
              <LayoutDashboard size={16} />
              Dashboard
            </button>
            <button
              onClick={() => setActiveTab("chat")}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                activeTab === "chat"
                  ? "bg-[#2a2f45] text-white shadow-sm"
                  : "text-slate-400 hover:text-slate-200"
              }`}
            >
              <MessageCircle size={16} />
              AI Chat
            </button>
          </nav>

          {/* Profile */}
          <div className="flex items-center gap-3">
            <div className="text-right">
              <p className="text-sm font-medium text-slate-200">{data.profile.name}</p>
              <p className="text-xs text-slate-500">
                ${data.profile.monthly_income.toLocaleString()}/mo
              </p>
            </div>
            <div className="w-9 h-9 bg-gradient-to-br from-emerald-400 to-teal-500 rounded-full flex items-center justify-center">
              <span className="text-white font-semibold text-sm">
                {data.profile.name.charAt(0)}
              </span>
            </div>
          </div>
        </div>
      </header>

      {/* Content */}
      <main className="max-w-7xl mx-auto px-6 py-6">
        {activeTab === "dashboard" ? (
          <Dashboard data={data} onExpenseAdded={fetchData} />
        ) : (
          <ChatPanel profile={data.profile} />
        )}
      </main>
    </div>
  );
}
