---
name: ref-frontend-conventions
description: Quy Æ°á»›c FE theo boundary frontend â€” app surface, API contract, cáº¥u trÃºc.
---

# Frontend Conventions Skill

## Khi dÃ¹ng

Boundary `layer: fe` / `kind: fe` (vÃ­ dá»¥ `fe-web`, `fe-admin`). Má»—i boundary FE **phá»¥c vá»¥** má»™t hoáº·c nhiá»u backend â€” ghi trong agent roster cá»™t `serves_boundaries`.

## Má»™t boundary FE = má»™t app surface

| `fe_surface` | ThÆ° má»¥c gá»£i Ã½ | Ghi chÃº |
|--------------|---------------|---------|
| `web-app` | `apps/{boundary_id}/` hoáº·c `apps/web/` | SPA chÃ­nh |
| `web-admin` | `apps/admin/` | Portal ná»™i bá»™ |
| `mobile` | `apps/mobile/` | React Native / Flutter |

Agent file: `agents/{boundary_id}-agent.md` â€” **khÃ´ng** gom chung `fe-agent.md` trá»« khi roster chá»‰ cÃ³ má»™t boundary `fe`.

## Quy Æ°á»›c báº¯t buá»™c

1. **UX** â€” implement theo `docs/architecture/ux/ux-{boundary_id}.md`.
2. **API** â€” chá»‰ gá»i contract `api-{backend}.md` cá»§a backend trong `serves_boundaries`.
3. **State** â€” feature state theo FEAT; shared UI kit theo ADR-004.
4. **Auth** â€” theo ADR-003 (token, refresh, route guard).
5. **KhÃ´ng** sá»­a `services/*` backend trá»« BFF thuá»™c boundary FE (náº¿u cÃ³).

## Cáº¥u trÃºc (React/Vue gá»£i Ã½)

```text
apps/{app}/
  src/
    features/       # theo FEAT
    shared/         # components, hooks
    api/            # client generated hoáº·c hand-written
    routes/
  package.json
packages/             # design system dÃ¹ng chung (náº¿u ADR cho phÃ©p)
```

## Done

- `serves_boundaries` khá»›p roster vÃ  `integrations-matrix.md`.
- Build/lint FE pass trÆ°á»›c `review-dev`.

