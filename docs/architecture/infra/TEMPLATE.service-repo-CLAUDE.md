# {{prefix}}-{{boundary}} — CLAUDE.md (service repo)

> Template scaffold cho service repo con (polyrepo). Dev sub-agent emit file nay vao `services/{{prefix}}-{{boundary}}/CLAUDE.md` lan dau scaffold boundary, substitute placeholder tu MATRIX entry.
> Placeholder: `{{prefix}}` `{{boundary}}` `{{kind}}` `{{stack}}` `{{repo_url}}` `{{owned_paths_md}}` `{{build_cmds}}`.

---

## Repo nay la gi

Service repo con cho boundary **{{boundary}}** (kind=`{{kind}}`), tach rieng theo chien luoc polyrepo. Day la code-repo standalone: chi chua code service + test, KHONG chua design.

Design source-of-truth song o **design-repo cha** (ADLC Design Harness). Khi mo session terminal rieng trong repo nay (ngoai luong orchestrator), doc design qua duong dan tuong doi `../../docs/architecture/` (xem muc Design reference). KHONG copy/snapshot design vao day.

## Identity

| Field | Value |
|---|---|
| Boundary | `{{boundary}}` |
| Kind | `{{kind}}` |
| Project prefix | `{{prefix}}` |
| Stack | {{stack}} |
| Service repo | `{{repo_url}}` |
| Working dir trong design-repo | `services/{{prefix}}-{{boundary}}/` (gitignored o design-repo) |

## Layout (theo kind)

```
{{prefix}}-{{boundary}}/
  CLAUDE.md                     # file nay
  .gitignore                    # tu TEMPLATE.service-repo-gitignore
  .claude/settings.json         # permission allowlist build tool theo kind
  # --- kind=backend (Java 21 + Spring Boot 3.4) ---
  build.gradle                  # Gradle default (Groovy DSL, KHÔNG kts); pom.xml chỉ khi ADR chọn Maven
  src/main/java/...             # code
  src/main/resources/           # application.yml, migrations
  src/test/java/...             # unit + integration test
  # --- kind=bff (Node 22 + Apollo) / kind=web (React 19 + Vite) ---
  package.json
  src/                          # source (resolver/schema cho bff; component/pages cho web)
  tests/ | src/__tests__/       # test
  # --- kind=mobile (Flutter 3) ---
  pubspec.yaml
  lib/                          # code
  test/                         # test
```

> Layout chi tiet trong (folder layer) theo HLD section 4 cua boundary (xem Design reference). Scaffold ref skill cua design-repo (ref-backend-pattern / ref-frontend-pattern / rules-{{kind}}) dinh nghia layout chuan.

## Design reference (READ-ONLY, KHONG snapshot)

Khi chay session rieng trong service repo, doc design tu design-repo cha qua duong dan tuong doi (service repo nam o `services/{{prefix}}-{{boundary}}/` nen design-repo root la `../../`):

| Can gi | Doc o (relative path tu service repo) |
|---|---|
| Project / stack / scope | `../../docs/architecture/PROJECT.md` |
| HLD boundary | `../../docs/architecture/hld/hld-{{boundary}}.md` |
| API contract | `../../docs/architecture/api/api-{{boundary}}.md` |
| Data model | `../../docs/architecture/data-model/data-model-{{boundary}}.md` |
| Event phat/nhan | `../../docs/architecture/events/{{boundary}}-events.md` |
| UX (kind=web/mobile) | `../../docs/architecture/ux/ux-{{boundary}}.md` |
| ADR | `../../docs/architecture/adr/ADR-*.md` |
| Knowledge graph | `../../knowledge-base/{{boundary}}.knowledge-graph.yaml` |
| Feature can implement | `../../docs/architecture/feat/FEAT-*.md` |

> Contract = file o `docs/architecture/{api,events,ux}/` cua design-repo. KHONG co contracts/ rieng, KHONG contract-hash/signing. Day la single-repo design: KHONG sync, KHONG translate, KHONG MANIFEST, KHONG docs-domain.

## Owned paths

Edit CHI trong cac pattern duoi (trong service repo nay):

{{owned_paths_md}}

> Day la cac path code/test/config cua service repo. Trong luong orchestrator (design-repo), boundary isolation duoc enforce boi PreToolUse hook theo `owned_paths` cua MATRIX entry.

## Non-negotiables (toi thieu)

1. **Edit chi trong owned_paths** cua repo nay (code + test + build file + config). KHONG dung toi file ngoai.
2. **KHONG sua design** — design song o design-repo cha (`../../docs/architecture/`), read-only tu day. Can doi design (contract drift / decision khac HLD) → submit Change Request ve design-repo (lenh `/apply-cr` tu DONE state), KHONG patch local roi quen.
3. **KHONG bypass test** — KHONG `--no-verify`, KHONG skip test. Build + test phai xanh truoc commit.
4. **KHONG hardcode secret** — dung env var / secrets manager (Azure Key Vault cho backend). Khong commit credential.
5. **Coverage >= 80** truoc khi handoff (theo gate dev-handoff cua design-repo).
6. **Decision non-trivial → ghi lai** — vao tracking cua design-repo (`../../tracking/decisions.md`) hoac note local roi dong bo ve CR. Khong de quyet dinh chi ton tai trong chat.
7. **Ngon ngu giao tiep = tieng Viet co dau**. Identifier code + framework keyword giu tieng Anh. KHONG icon/emoji trong tai lieu.

## Build / Test

```bash
{{build_cmds}}
```

> `{{build_cmds}}` substitute theo kind:
> - backend: `./gradlew build` (compile + unit) · `./gradlew integrationTest` · `./gradlew test jacocoTestReport` (coverage) — hoac `mvn` tuong duong
> - bff / web: `pnpm install` · `pnpm build` · `pnpm test --coverage` · `pnpm lint`
> - mobile: `flutter pub get` · `flutter build` · `flutter test --coverage` · `flutter analyze`

## Authority

Moi design decision defer ve design-repo cha. Service repo chi implement AC trong FEAT theo HLD/API/contract. Khong tu mo rong scope; scope-change qua CR.
