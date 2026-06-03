# Frontend Guide

> Everything about the Next.js 15 frontend. Read this when working on React components, pages, or data fetching.

---

## Tech Stack

| Technology | Version | Purpose |
|------------|---------|---------|
| Next.js | 15 | App Router, API rewrites, standalone output |
| React | 19 | UI framework |
| TypeScript | 5.6 | Type safety |
| Tailwind CSS | 4 | Utility-first CSS |
| Recharts | 2.15 | Charts (price history) |
| Lucide React | 0.460 | Icons |

---

## Entry Points

| File | Purpose |
|------|---------|
| `project/frontend/next.config.ts` | Standalone output, API rewrites to backend |
| `project/frontend/package.json` | Dependencies and scripts |
| `project/frontend/tsconfig.json` | TypeScript config with path alias `@/*` |
| `project/frontend/postcss.config.mjs` | Tailwind v4 PostCSS plugin |
| `project/frontend/app/globals.css` | Tailwind directives, base styles |
| `project/frontend/app/layout.tsx` | Root layout with sidebar |

---

## API Communication

All backend communication goes through **`lib/api.ts`**. Never hardcode API URLs in components.

### `lib/api.ts` — API Client

Uses `fetch` with:
- Base URL from `NEXT_PUBLIC_API_URL` env var
- JWT token from `localStorage` (key: `token`)
- JSON content type by default

```typescript
// Example usage in a component
import { api } from "@/lib/api";

const items = await api.get("/items");
const item = await api.post("/items", { name: "...", ... });
```

### `lib/hooks.ts` — Data Hooks

Custom React hooks wrapping `api.ts` with loading/error states:

```typescript
import { useItems, useDeals, useStats } from "@/lib/hooks";

// In a component:
const { data: items, loading, error } = useItems();
const { data: stats } = useStats();
```

**Adding a new hook:** Follow the existing pattern — use `useEffect` + `useState`, call `api.get()` or `api.post()`, handle loading/error states.

---

## Routing (Next.js App Router)

All pages are in `project/frontend/app/` using the App Router convention.

| Route | File | Purpose |
|-------|------|---------|
| `/` | `app/page.tsx` | Dashboard — API usage bar, stats cards, top deals |
| `/items` | `app/items/page.tsx` | Tracked items table with inline interval editor |
| `/items/add` | `app/items/add/page.tsx` | 3-step Add Item Wizard |
| `/deals` | `app/deals/page.tsx` | Deals feed with scoring details |
| `/alerts` | `app/alerts/page.tsx` | Alert history with dismiss action |
| `/settings` | `app/settings/page.tsx` | Notification settings (Telegram, SMTP) |
| `/history` | `app/history/page.tsx` | Price history charts |

### Adding a New Page

1. Create `project/frontend/app/<route>/page.tsx`:
```typescript
export default function MyPage() {
  return <div>My Page</div>;
}
```

2. Add navigation link in `components/sidebar.tsx`

3. Add API integration in `lib/api.ts` and `lib/hooks.ts` if needed

---

## Shared Components

### `components/sidebar.tsx` — Navigation

- Fixed left sidebar, 256px wide
- Active link highlighted with `bg-indigo-50 text-indigo-700`
- 7 nav items with Lucide icons
- Uses Next.js `usePathname()` for active state

**Adding a nav item:**
```typescript
const navItems = [
  // ... existing items
  { href: "/my-page", label: "My Page", icon: MyIcon },
];
```

### `components/stats-card.tsx` — Dashboard Stat Cards

Accepts:
- `title: string` — Card label
- `value: string | number` — Main stat
- `subtitle?: string` — Secondary info
- `trend?: { value: number; positive: boolean }` — Trend indicator

### `components/api-usage-bar.tsx` — API Budget Tracker

Accepts:
- `used: number` — Current API calls today
- `limit: number` — Daily limit (default 5000)
- `threshold: number` — Warning threshold (default 4000)

Visual states:
- Green: `< 80%`
- Yellow: `80-95%`
- Red: `> 95%`

---

## Page Patterns

### Dashboard (`app/page.tsx`)

Layout:
```
┌──────────────────────────────────────────────┐
│  API Usage Bar (full width)                  │
├──────────────┬──────────────┬────────────────┤
│  Stats Card  │  Stats Card  │  Stats Card    │
│  (total)     │  (active)    │  (alerts)      │
├──────────────┴──────────────┴────────────────┤
│  Top Deals (table)                           │
├──────────────────────────────────────────────┤
│  Quick Actions (buttons)                     │
└──────────────────────────────────────────────┘
```

### Items List (`app/items/page.tsx`)

- Table with all tracked items
- Columns: Name, Category, Target Price, Interval, Priority, Status, Actions
- **Inline interval editor**: Click interval value → select new value → auto-save
- **Priority badge**: P0=red, P1=orange, P2=blue, P3=gray
- **Toggle switch**: Enable/disable tracking
- **Delete button**: With confirmation

### Add Item Wizard (`app/items/add/page.tsx`)

3-step wizard:
1. **Select Component**: Search box with catalog auto-suggest → `GET /catalog?q=...`
2. **Configure**: Target price (pre-filled from catalog), polling interval selector (with presets: Hot/Standard/Monitor/Passive), notes field
3. **Review**: Summary card, scam floor warning if target < floor, submit → `POST /items`

---

## Styling Conventions

- **Colors**: Use Tailwind's slate/indigo palette. No arbitrary colors.
- **Spacing**: 4-unit increments (`p-4`, `gap-6`, `mb-2`)
- **Typography**: Inter font (loaded via `next/font/google` in layout.tsx)
- **Cards**: `bg-white rounded-lg border border-slate-200 shadow-sm`
- **Buttons**: `bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg`
- **Inputs**: `border-slate-300 rounded-lg focus:ring-indigo-500 focus:border-indigo-500`
- **Badges**: Rounded pills with priority colors

---

## Data Fetching Patterns

### Client Components (most pages)

```typescript
"use client";
import { useState, useEffect } from "react";
import { api } from "@/lib/api";

export default function MyPage() {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get("/my-endpoint").then(setData).finally(() => setLoading(false));
  }, []);

  if (loading) return <div>Loading...</div>;
  return <div>{data.map(...)}</div>;
}
```

### Using the hooks pattern (preferred)

```typescript
"use client";
import { useMyData } from "@/lib/hooks";

export default function MyPage() {
  const { data, loading, error } = useMyData();
  // ...
}
```

---

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `NEXT_PUBLIC_API_URL` | Yes | Backend API base URL |

**Only `NEXT_PUBLIC_*` vars are available in the browser.** All other env vars must be used server-side.

---

## Common Tasks

### Add a new page
1. Create `app/<route>/page.tsx`
2. Add to sidebar nav items
3. Add API methods to `lib/api.ts` if backend calls needed
4. Add hook to `lib/hooks.ts` if using the hook pattern

### Add a new component
1. Create `components/my-component.tsx`
2. Export default function
3. Import in page files that need it

### Connect to a new backend endpoint
1. Add method to `lib/api.ts`
2. Optionally add hook to `lib/hooks.ts`
3. Use in page/component via hook or direct `api.*` call

### Style a new element
- Reference existing components for patterns
- Use Tailwind utility classes
- Prefer `slate-*` for neutrals, `indigo-*` for brand/accent
- No arbitrary values (`w-[123px]`) without good reason
