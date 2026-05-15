"use client";

export default function SettingsPage() {
  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <h1 className="text-2xl font-bold text-slate-800">Settings</h1>
      <div className="bg-white rounded-xl border p-6">
        <h2 className="text-lg font-semibold mb-4">Notifications</h2>
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div><p className="font-medium">Telegram Alerts</p><p className="text-xs text-slate-500">Instant deal alerts via Telegram bot</p></div>
            <span className="text-xs text-slate-400">Configure via .env</span>
          </div>
          <div className="flex items-center justify-between">
            <div><p className="font-medium">Email Digest</p><p className="text-xs text-slate-500">Daily summary of top deals</p></div>
            <span className="text-xs text-slate-400">Configure via .env</span>
          </div>
        </div>
      </div>
      <div className="bg-white rounded-xl border p-6">
        <h2 className="text-lg font-semibold mb-4">About</h2>
        <p className="text-sm text-slate-500">Hardware Deal Tracker v0.2.0</p>
        <p className="text-sm text-slate-500">34 tracked items with validated pricing</p>
        <p className="text-sm text-slate-500">Tiered polling with eBay API rate limiting</p>
      </div>
    </div>
  );
}
