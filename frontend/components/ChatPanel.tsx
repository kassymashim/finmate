"use client";

import { useState, useRef, useEffect } from "react";
import { Send, Sparkles, Plus } from "lucide-react";

interface Message {
  role: "user" | "assistant";
  content: string;
  intent?: string;
}

interface Props {
  profile: {
    name: string;
    monthly_income: number;
    current_savings: number;
    savings_goal: number;
    financial_goals: string[];
  };
}

const SUGGESTED_QUESTIONS = [
  "Where is my money going?",
  "How can I save $15,000 for a down payment?",
  "Am I spending too much on restaurants?",
  "Create a budget plan for me",
  "What's my savings rate?",
];

export default function ChatPanel({ profile }: Props) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const sendMessage = async (text: string) => {
    if (!text.trim()) return;

    const userMsg: Message = { role: "user", content: text };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setLoading(true);

    try {
      const history = messages.map((m) => ({ role: m.role, content: m.content }));
      const res = await fetch("http://localhost:8003/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: text, history }),
      });
      const data = await res.json();
      setMessages((prev) => [...prev, { role: "assistant", content: data.response, intent: data.intent }]);
    } catch {
      setMessages((prev) => [...prev, { role: "assistant", content: "Sorry, couldn't connect to the API." }]);
    }

    setLoading(false);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage(input);
    }
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-4 gap-6 h-[calc(100vh-140px)]">
      {/* Chat Area */}
      <div className="lg:col-span-3 bg-[#1e2235] rounded-2xl border border-[#2a2f45] flex flex-col">
        {/* Header */}
        <div className="px-6 py-4 border-b border-[#2a2f45]">
          <div className="flex items-center gap-2">
            <Sparkles size={18} className="text-indigo-400" />
            <h2 className="font-semibold text-white">Chat with FinMate</h2>
          </div>
          <p className="text-xs text-slate-500 mt-0.5">
            Ask about your finances, get personalized advice
          </p>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto px-6 py-4 space-y-4">
          {messages.length === 0 && (
            <div className="flex flex-col items-center justify-center h-full text-center">
              <div className="w-16 h-16 bg-indigo-500/10 rounded-2xl flex items-center justify-center mb-4">
                <Sparkles size={28} className="text-indigo-400" />
              </div>
              <h3 className="text-lg font-semibold text-slate-200 mb-1">
                Hi {profile.name.split(" ")[0]}! How can I help?
              </h3>
              <p className="text-sm text-slate-500 mb-6 max-w-md">
                I can analyze your spending, create budgets, and set savings goals.
              </p>
              <div className="flex flex-wrap gap-2 justify-center max-w-lg">
                {SUGGESTED_QUESTIONS.map((q) => (
                  <button
                    key={q}
                    onClick={() => sendMessage(q)}
                    className="px-3 py-2 bg-[#2a2f45] hover:bg-indigo-500/20 border border-[#3a3f55] hover:border-indigo-500/30 rounded-xl text-xs text-slate-300 hover:text-indigo-300 transition-all"
                  >
                    {q}
                  </button>
                ))}
              </div>
            </div>
          )}

          {messages.map((msg, i) => (
            <div key={i} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
              <div className={`max-w-[80%] px-4 py-3 text-sm leading-relaxed ${msg.role === "user" ? "chat-bubble-user" : "chat-bubble-ai"}`}>
                <div className="whitespace-pre-wrap">{msg.content}</div>
                {msg.intent && (
                  <span className="inline-block mt-2 px-2 py-0.5 bg-indigo-500/20 text-indigo-300 text-[10px] font-medium rounded-full">
                    {msg.intent}
                  </span>
                )}
              </div>
            </div>
          ))}

          {loading && (
            <div className="flex justify-start">
              <div className="chat-bubble-ai px-4 py-3">
                <div className="flex gap-1.5">
                  <div className="w-2 h-2 bg-slate-500 rounded-full animate-bounce" />
                  <div className="w-2 h-2 bg-slate-500 rounded-full animate-bounce [animation-delay:0.1s]" />
                  <div className="w-2 h-2 bg-slate-500 rounded-full animate-bounce [animation-delay:0.2s]" />
                </div>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Input */}
        <div className="px-6 py-4 border-t border-[#2a2f45]">
          <div className="flex items-center gap-3">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask about your finances..."
              className="flex-1 px-4 py-3 bg-[#0f1117] border border-[#2a2f45] rounded-xl text-sm text-white focus:outline-none focus:ring-2 focus:ring-indigo-500 placeholder:text-slate-500"
              disabled={loading}
            />
            <button
              onClick={() => sendMessage(input)}
              disabled={!input.trim() || loading}
              className="w-11 h-11 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-xl flex items-center justify-center text-white hover:opacity-90 transition-opacity disabled:opacity-40"
            >
              <Send size={18} />
            </button>
          </div>
        </div>
      </div>

      {/* Side Panel */}
      <div className="lg:col-span-1 space-y-4">
        <div className="bg-[#1e2235] rounded-2xl border border-[#2a2f45] p-5">
          <h3 className="text-sm font-semibold text-slate-300 mb-3">Your Profile</h3>
          <div className="space-y-2 text-xs text-slate-400">
            <div className="flex justify-between">
              <span>Monthly Income</span>
              <span className="font-semibold text-slate-200">${profile.monthly_income.toLocaleString()}</span>
            </div>
            <div className="flex justify-between">
              <span>Current Savings</span>
              <span className="font-semibold text-slate-200">${profile.current_savings.toLocaleString()}</span>
            </div>
            <div className="flex justify-between">
              <span>Savings Goal</span>
              <span className="font-semibold text-slate-200">${profile.savings_goal.toLocaleString()}</span>
            </div>
            <div className="pt-2">
              <div className="flex justify-between text-[10px] text-slate-500 mb-1">
                <span>Progress</span>
                <span>{Math.round((profile.current_savings / profile.savings_goal) * 100)}%</span>
              </div>
              <div className="w-full h-2 bg-[#0f1117] rounded-full overflow-hidden">
                <div
                  className="h-full bg-gradient-to-r from-indigo-500 to-purple-500 rounded-full"
                  style={{ width: `${Math.min(100, (profile.current_savings / profile.savings_goal) * 100)}%` }}
                />
              </div>
            </div>
          </div>
        </div>

        <div className="bg-[#1e2235] rounded-2xl border border-[#2a2f45] p-5">
          <h3 className="text-sm font-semibold text-slate-300 mb-3">Financial Goals</h3>
          <div className="space-y-2">
            {profile.financial_goals.map((goal, i) => (
              <div key={i} className="flex items-start gap-2 text-xs text-slate-400">
                <div className="w-4 h-4 mt-0.5 rounded-full border-2 border-indigo-400/50 flex-shrink-0" />
                <span>{goal}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
