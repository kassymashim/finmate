"use client";

import { useState } from "react";
import { DashboardData } from "@/app/page";
import {
  PieChart,
  Pie,
  Cell,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  AreaChart,
  Area,
  CartesianGrid,
} from "recharts";
import {
  TrendingDown,
  TrendingUp,
  Wallet,
  PiggyBank,
  CreditCard,
  Plus,
  Check,
  ChevronDown,
} from "lucide-react";

const COLORS: Record<string, string> = {
  Housing: "#6366f1",
  Groceries: "#10b981",
  Restaurants: "#f59e0b",
  Transportation: "#3b82f6",
  Utilities: "#8b5cf6",
  Entertainment: "#ec4899",
  Shopping: "#ef4444",
  Healthcare: "#14b8a6",
  Subscriptions: "#f97316",
  Other: "#6b7280",
};

const COLOR_LIST = [
  "#6366f1", "#10b981", "#f59e0b", "#3b82f6", "#8b5cf6",
  "#ec4899", "#ef4444", "#14b8a6", "#f97316", "#6b7280",
];

const MONTH_NAMES = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

interface Props {
  data: DashboardData;
  onExpenseAdded: () => void;
}

function MetricCard({
  label,
  value,
  icon: Icon,
  trend,
  color = "indigo",
}: {
  label: string;
  value: string;
  icon: any;
  trend?: string;
  color?: string;
}) {
  const colorClasses: Record<string, string> = {
    indigo: "from-indigo-500 to-indigo-600",
    emerald: "from-emerald-500 to-emerald-600",
    rose: "from-rose-500 to-rose-600",
    amber: "from-amber-500 to-amber-600",
    blue: "from-blue-500 to-blue-600",
  };

  return (
    <div className="bg-[#1e2235] rounded-2xl border border-[#2a2f45] p-5 hover:border-[#3a3f55] transition-all">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-[11px] font-medium text-slate-500 uppercase tracking-wider">
            {label}
          </p>
          <p className="text-2xl font-bold text-white mt-1">{value}</p>
          {trend && <p className="text-xs text-slate-500 mt-1">{trend}</p>}
        </div>
        <div className={`w-10 h-10 bg-gradient-to-br ${colorClasses[color]} rounded-xl flex items-center justify-center opacity-80`}>
          <Icon size={20} className="text-white" />
        </div>
      </div>
    </div>
  );
}

function CustomTooltip({ active, payload, label }: any) {
  if (!active || !payload?.length) return null;
  return (
    <div className="bg-[#1e2235] shadow-xl rounded-xl border border-[#2a2f45] p-3 text-xs">
      <p className="font-semibold text-slate-300 mb-1">{label}</p>
      {payload.map((entry: any, i: number) => (
        <p key={i} style={{ color: entry.color }} className="font-medium">
          {entry.name}: ${entry.value?.toLocaleString()}
        </p>
      ))}
    </div>
  );
}

export default function Dashboard({ data, onExpenseAdded }: Props) {
  const { categories, monthlyTrends, dailySpending, recentTransactions, allTransactions, availableMonths } = data;

  const [selectedMonth, setSelectedMonth] = useState<string>(availableMonths?.[0] || "");
  const [showAddExpense, setShowAddExpense] = useState(false);
  const [expenseInput, setExpenseInput] = useState("");
  const [addSuccess, setAddSuccess] = useState<string | null>(null);

  // Filter data by selected month, sort newest first
  const filteredTransactions = (allTransactions || recentTransactions)
    .filter((t) => t.date.startsWith(selectedMonth))
    .sort((a, b) => b.date.localeCompare(a.date));
  const monthExpenses = filteredTransactions.filter((t) => t.amount < 0);

  // Calculate KPIs for selected month
  const monthTotalSpent = monthExpenses.reduce((sum, t) => sum + Math.abs(t.amount), 0);
  const monthCategories = monthExpenses.reduce<Record<string, number>>((acc, t) => {
    acc[t.category] = (acc[t.category] || 0) + Math.abs(t.amount);
    return acc;
  }, {});
  const monthCategoryData = Object.entries(monthCategories)
    .map(([name, amount]) => ({ name, amount: Math.round(amount * 100) / 100 }))
    .sort((a, b) => b.amount - a.amount);

  const topCategory = monthCategoryData[0]?.name || "N/A";
  const txnCount = monthExpenses.length;
  const avgPerTxn = txnCount > 0 ? monthTotalSpent / txnCount : 0;

  // Format month for display
  const formatMonth = (m: string) => {
    if (!m) return "";
    const [year, month] = m.split("-");
    return `${MONTH_NAMES[parseInt(month) - 1]} ${year}`;
  };

  // All categories in monthly trends
  const allCategoriesInTrends = [...new Set(monthlyTrends.flatMap((m) => Object.keys(m).filter((k) => k !== "month")))];

  // Handle quick add expense
  const handleAddExpense = async () => {
    if (!expenseInput.trim()) return;

    const match = expenseInput.match(/^(.+?)\s*\$?([\d]+\.?\d*)\s*$/);
    if (!match) return;

    const merchant = match[1].trim();
    const amount = parseFloat(match[2]);

    try {
      const res = await fetch("http://localhost:8003/api/expense", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ merchant, amount }),
      });
      const result = await res.json();
      setAddSuccess(`${result.merchant} — $${result.amount} → ${result.category}`);
      setExpenseInput("");
      setTimeout(() => {
        setAddSuccess(null);
        setShowAddExpense(false);
        onExpenseAdded();
      }, 2000);
    } catch {
      setAddSuccess("Error adding expense");
    }
  };

  return (
    <div className="space-y-6">
      {/* Top Bar: Month Filter + Add Expense */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <h2 className="text-xl font-bold text-white">Overview</h2>
          <div className="relative">
            <select
              value={selectedMonth}
              onChange={(e) => setSelectedMonth(e.target.value)}
              className="appearance-none bg-[#1e2235] border border-[#2a2f45] rounded-xl px-4 py-2 pr-8 text-sm text-slate-200 focus:outline-none focus:ring-2 focus:ring-indigo-500 cursor-pointer"
            >
              {(availableMonths || []).map((m) => (
                <option key={m} value={m}>
                  {formatMonth(m)}
                </option>
              ))}
            </select>
            <ChevronDown size={14} className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-500 pointer-events-none" />
          </div>
        </div>

        {/* Add Expense Button */}
        <div className="flex items-center gap-3">
          {showAddExpense && (
            <div className="flex items-center gap-2 animate-in slide-in-from-right">
              <input
                type="text"
                value={expenseInput}
                onChange={(e) => setExpenseInput(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleAddExpense()}
                placeholder='e.g. "Chipotle 15"'
                className="bg-[#1e2235] border border-[#2a2f45] rounded-xl px-4 py-2 text-sm text-white placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 w-56"
                autoFocus
              />
              <button
                onClick={handleAddExpense}
                className="w-9 h-9 bg-indigo-500 hover:bg-indigo-600 rounded-xl flex items-center justify-center text-white transition-colors"
              >
                <Check size={16} />
              </button>
            </div>
          )}
          {addSuccess && (
            <span className="text-xs text-emerald-400 font-medium bg-emerald-500/10 px-3 py-1.5 rounded-lg">
              ✓ {addSuccess}
            </span>
          )}
          <button
            onClick={() => setShowAddExpense(!showAddExpense)}
            className={`flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-medium transition-all ${
              showAddExpense
                ? "bg-[#2a2f45] text-slate-300"
                : "bg-indigo-500 hover:bg-indigo-600 text-white"
            }`}
          >
            <Plus size={16} />
            Add Expense
          </button>
        </div>
      </div>

      {/* Metrics Row - Current Month */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
        <MetricCard
          label="Spent This Month"
          value={`$${monthTotalSpent.toLocaleString(undefined, { maximumFractionDigits: 0 })}`}
          icon={CreditCard}
          trend={formatMonth(selectedMonth)}
          color="rose"
        />
        <MetricCard
          label="Transactions"
          value={txnCount.toString()}
          icon={TrendingDown}
          trend={`In ${formatMonth(selectedMonth)}`}
          color="blue"
        />
        <MetricCard
          label="Avg per Transaction"
          value={`$${avgPerTxn.toFixed(0)}`}
          icon={Wallet}
          trend="Average spend"
          color="amber"
        />
        <MetricCard
          label="Top Category"
          value={topCategory}
          icon={TrendingUp}
          trend={monthCategoryData[0] ? `$${monthCategoryData[0].amount.toLocaleString()}` : ""}
          color="indigo"
        />
        <MetricCard
          label="Categories"
          value={monthCategoryData.length.toString()}
          icon={PiggyBank}
          trend="Active this month"
          color="emerald"
        />
      </div>

      {/* Charts Row 1 */}
      <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
        {/* Donut Chart */}
        <div className="lg:col-span-2 bg-[#1e2235] rounded-2xl border border-[#2a2f45] p-6">
          <h3 className="text-sm font-semibold text-slate-300 mb-4">
            Spending by Category — {formatMonth(selectedMonth)}
          </h3>
          <ResponsiveContainer width="100%" height={240}>
            <PieChart>
              <Pie
                data={monthCategoryData}
                cx="50%"
                cy="50%"
                innerRadius={60}
                outerRadius={100}
                dataKey="amount"
                nameKey="name"
                stroke="none"
              >
                {monthCategoryData.map((entry, index) => (
                  <Cell
                    key={entry.name}
                    fill={COLORS[entry.name] || COLOR_LIST[index % COLOR_LIST.length]}
                  />
                ))}
              </Pie>
              <Tooltip
                formatter={(value: number) => [`$${value.toLocaleString()}`, ""]}
                contentStyle={{
                  borderRadius: "12px",
                  border: "1px solid #2a2f45",
                  backgroundColor: "#1e2235",
                  color: "#f1f5f9",
                }}
              />
            </PieChart>
          </ResponsiveContainer>
          {/* Legend */}
          <div className="grid grid-cols-2 gap-2 mt-2">
            {monthCategoryData.slice(0, 8).map((cat, i) => (
              <div key={cat.name} className="flex items-center gap-2 text-xs">
                <div
                  className="w-2.5 h-2.5 rounded-full flex-shrink-0"
                  style={{ backgroundColor: COLORS[cat.name] || COLOR_LIST[i] }}
                />
                <span className="text-slate-400 truncate">{cat.name}</span>
                <span className="text-slate-500 ml-auto">${cat.amount.toLocaleString()}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Monthly Trend - All Months */}
        <div className="lg:col-span-3 bg-[#1e2235] rounded-2xl border border-[#2a2f45] p-6">
          <h3 className="text-sm font-semibold text-slate-300 mb-4">
            Monthly Spending Trend
          </h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={monthlyTrends} margin={{ top: 5, right: 10, left: 10, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#2a2f45" />
              <XAxis
                dataKey="month"
                tick={{ fontSize: 11, fill: "#64748b" }}
                tickFormatter={(v) => {
                  const parts = v.split("-");
                  return MONTH_NAMES[parseInt(parts[1]) - 1];
                }}
                axisLine={{ stroke: "#2a2f45" }}
              />
              <YAxis tick={{ fontSize: 11, fill: "#64748b" }} tickFormatter={(v) => `$${v}`} axisLine={{ stroke: "#2a2f45" }} />
              <Tooltip content={<CustomTooltip />} />
              {allCategoriesInTrends.map((cat, i) => (
                <Bar
                  key={cat}
                  dataKey={cat}
                  stackId="a"
                  fill={COLORS[cat] || COLOR_LIST[i % COLOR_LIST.length]}
                  radius={i === allCategoriesInTrends.length - 1 ? [4, 4, 0, 0] : [0, 0, 0, 0]}
                />
              ))}
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Charts Row 2 */}
      <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
        {/* Daily Spending Area */}
        <div className="lg:col-span-3 bg-[#1e2235] rounded-2xl border border-[#2a2f45] p-6">
          <h3 className="text-sm font-semibold text-slate-300 mb-4">
            Daily Spending
          </h3>
          <ResponsiveContainer width="100%" height={200}>
            <AreaChart data={dailySpending} margin={{ top: 5, right: 10, left: 10, bottom: 5 }}>
              <defs>
                <linearGradient id="colorAmount" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#6366f1" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#6366f1" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#2a2f45" />
              <XAxis
                dataKey="date"
                tick={{ fontSize: 10, fill: "#64748b" }}
                tickFormatter={(v) => v.slice(5)}
                axisLine={{ stroke: "#2a2f45" }}
              />
              <YAxis tick={{ fontSize: 10, fill: "#64748b" }} tickFormatter={(v) => `$${v}`} axisLine={{ stroke: "#2a2f45" }} />
              <Tooltip
                formatter={(value: number) => [`$${value.toFixed(0)}`, "Spent"]}
                contentStyle={{ borderRadius: "12px", border: "1px solid #2a2f45", backgroundColor: "#1e2235", color: "#f1f5f9" }}
              />
              <Area
                type="monotone"
                dataKey="amount"
                stroke="#6366f1"
                strokeWidth={2}
                fill="url(#colorAmount)"
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        {/* Recent Transactions for selected month */}
        <div className="lg:col-span-2 bg-[#1e2235] rounded-2xl border border-[#2a2f45] p-6">
          <h3 className="text-sm font-semibold text-slate-300 mb-4">
            Transactions — {formatMonth(selectedMonth)}
          </h3>
          <div className="space-y-2 max-h-[220px] overflow-y-auto">
            {monthExpenses.slice(0, 15).map((txn, i) => (
              <div
                key={i}
                className="flex items-center justify-between py-2 border-b border-[#2a2f45] last:border-0"
              >
                <div className="flex items-center gap-3">
                  <div
                    className="w-8 h-8 rounded-lg flex items-center justify-center text-xs font-bold text-white"
                    style={{ backgroundColor: COLORS[txn.category] || "#6b7280" }}
                  >
                    {txn.category.charAt(0)}
                  </div>
                  <div>
                    <p className="text-sm font-medium text-slate-200">{txn.merchant}</p>
                    <p className="text-[11px] text-slate-500">{txn.date} • {txn.category}</p>
                  </div>
                </div>
                <span className="text-sm font-semibold text-rose-400">
                  -${Math.abs(txn.amount).toFixed(2)}
                </span>
              </div>
            ))}
            {monthExpenses.length === 0 && (
              <p className="text-sm text-slate-500 text-center py-8">No transactions for this month</p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
