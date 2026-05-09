# MicTest12 Dashboard

A full-featured React admin dashboard built with Vite, TypeScript, React Router, and Recharts.

## Features

- Five pages: **Overview**, **Analytics**, **Users**, **Orders**, **Settings**
- Sidebar navigation with collapsible layout (mobile-friendly drawer)
- Top header with search, theme toggle, notifications, and avatar
- KPI stat cards with trend indicators
- Charts: revenue area chart, weekly activity bars, traffic-by-channel donut
- Sortable, filterable tables for users and orders
- Status badges, activity feed, ranked lists
- Settings page with profile form, theme picker, notification toggles, and danger zone
- Light & dark themes (auto-detected, persisted to localStorage)
- Fully responsive layout

## Getting started

```bash
cd dashboard
npm install
npm run dev
```

Open <http://localhost:5173> in your browser.

## Build

```bash
npm run build      # type-check + production build
npm run preview    # preview the production build
```

## Project structure

```
dashboard/
├── index.html
├── package.json
├── tsconfig.json
├── vite.config.ts
└── src/
    ├── App.tsx
    ├── main.tsx
    ├── index.css
    ├── components/
    │   ├── ActivityChart.tsx
    │   ├── Card.tsx
    │   ├── ChannelChart.tsx
    │   ├── Header.tsx
    │   ├── RevenueChart.tsx
    │   ├── Sidebar.tsx
    │   └── StatCard.tsx
    ├── context/
    │   └── ThemeContext.tsx
    ├── data/
    │   └── mockData.ts
    └── pages/
        ├── Analytics.tsx
        ├── Orders.tsx
        ├── Overview.tsx
        ├── Settings.tsx
        └── Users.tsx
```

The data layer (`src/data/mockData.ts`) is a single module of typed mock data — swap it for API calls when connecting to a backend.
