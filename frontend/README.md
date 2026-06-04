# Frontend — Archsari

Vite + React SPA for the architecture planning wizard.

## Folder structure

```
src/
├── main.jsx                 # Entry point
├── App.jsx                  # Auth gate + app shell wiring
├── api/                     # HTTP client and endpoint modules
├── components/
│   ├── layout/              # AppShell, Sidebar, Topbar
│   ├── ui/                  # Badge, Spinner, ErrorBanner
│   └── wizard/              # Step forms, actions, notices
├── pages/                   # Full-screen views (Login, loading)
├── features/
│   └── architecture/        # Architecture document feature
│       ├── components/      # Workspace, document sections, diagrams
│       └── utils/           # Cost derivation, architecture helpers
├── hooks/                   # useWizard, useProjectTypes, useDocumentSections
├── context/                 # AuthContext
├── constants/               # Wizard options, document sections, costs
├── utils/                   # Validation, text formatting
├── types/                   # JSDoc typedefs
└── styles/                  # CSS partials (base, layout, wizard, document, …)
```

## Layer responsibilities

| Layer | Responsibility |
|-------|----------------|
| **pages** | Full-screen routes (login, loading) |
| **components/layout** | App chrome — sidebar, topbar, shell |
| **components/wizard** | Step 1–2 forms and navigation actions |
| **features/architecture** | Step 3 document workspace and all sections |
| **hooks** | Wizard state, API data fetching, scroll spy |
| **api** | All fetch calls — components never call fetch directly |
| **constants** | Labels, options, defaults, cost bands |
| **utils** | Pure helpers (validation, text formatting) |

## Running locally

```bash
cd frontend
npm install
npm run dev
```

Proxies `/api` to the backend at `http://127.0.0.1:8000`.

## Build

```bash
npm run build
npm run preview
```
