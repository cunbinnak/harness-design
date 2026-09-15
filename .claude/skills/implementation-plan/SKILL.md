---
name: implementation-plan
description: Stage PLAN (/domain, program-planner) — WAVE-SEQUENCE + wave-{N}.md cho MỌI wave (full plan toàn dự án, nhiều wave=sprint phụ thuộc nhau) + materialize MATRIX + KG skeleton. Sau DESIGN, trước REVIEW.
---

# Implementation Plan Skill

## Khi load
Command **`/domain`** (stage **PLAN** → REVIEW) — agent `program-planner-agent`, sau `/domain`.
Input: `docs/architecture/PROJECT.md` (Discovery D3) + product DOMAIN (`epics/`, `feat/` AC+BR, `business-rules/`, `journeys/`, `personas/`) + design (`adr/HLD/api/data-model/integrations/ux/events`) + charter boundaries (`docs/discovery/boundaries/*/CHARTER.md`).
WAVE-SEQUENCE theo `docs/plans/TEMPLATE.WAVE-SEQUENCE.md` (clone ADLC, adapt single-repo): có field `wave_class`/`wave_strategy`/`target_count_per_layer` + block YAML per-wave (`### §wave-NNN`) + `targets`=boundary_id từ MATRIX + contract trỏ `docs/architecture/{api,events,ux}/` — điền theo template. `start-wave` đọc wave-number → boundaries từ MATRIX; còn `wave_class`/`wave_strategy`/`targets` **được gate `wave_sequence_lint` ở `/domain`** (enum + cap≤3 + strategy layer-purity + vertical parent_epic + inherited_active file tồn tại) → phải điền §2 block YAML đúng schema.

## Wave = sprint — dự án chia thành NHIỀU wave
- **1 wave = 1 sprint** giao được 1 lát sản phẩm chạy end-to-end.
- **Dự án luôn chia thành nhiều wave** (≥ 2 khi có phụ thuộc) — KHÔNG gom hết mọi boundary/FEAT vào 1 wave.
- **Wave sau phụ thuộc wave trước** (tính năng này chờ tính năng khác): vd `order` chờ `auth` + `catalog`; `payment` chờ `order`; `customer-app` chờ API order/catalog.
- **Intake sinh FULL PLAN toàn dự án**: WAVE-SEQUENCE + **chi tiết MỌI wave** (`wave-001.md … wave-00N.md`) ngay từ đầu.

## Deliverable của /domain (đúng cái gate plan verify)
1. **`docs/plans/WAVE-SEQUENCE.md`** — **roadmap toàn dự án** theo `TEMPLATE.WAVE-SEQUENCE.md`: chia **toàn bộ** boundary/FEAT thành **nhiều wave** theo phụ thuộc. Mỗi wave: goal + boundaries in scope + features + **dependencies (cần gì từ wave trước)** + estimated effort + exit criteria. (Wave 1, Wave 2, Wave 3, …)
2. **`docs/plans/wave-001.md` … `wave-00N.md`** — chi tiết **MỌI wave** (mỗi wave 1 file theo `TEMPLATE.wave.md`): boundaries in scope, FEAT + AC count, thứ tự dev (foundation trước), cross-wave dependency, exit criteria. *(Scope đổi về sau → refine wave-{N}.md qua `/domain`.)*
3. **`harness/SERVICE-BOUNDARY-MATRIX.json`** — materialize từ decomposition: **≥ 1 boundary**, mỗi boundary `{boundary_id, kind, prefix, tech{language,framework,data_store}, wave, features[], features_by_wave{}, ref_skills[], depends_on, consumed_by}` (+ `owned_paths`/`repo_url` nếu có).
   - `features[]` = **toàn bộ** FEAT-id boundary sẽ đảm nhận, cộng dồn qua mọi wave (backlog đầy đủ của boundary đó).
   - **`features_by_wave`** (BẮT BUỘC nếu boundary sống qua ≥2 wave — tức boundary đó còn nhận thêm FEAT ở wave sau): `{"<wave_n>": [feat_id,...]}` — tách đúng FEAT nào thuộc wave nào. **Thiếu field này mà boundary có ≥2 wave → `wave_features_from_matrix` trả TOÀN BỘ `features[]` cho MỌI wave nó khớp** (bug thật đã gặp: FEAT "Deferred to later waves" ở wave-{N}.md vẫn lọt vào `STATE.wave_features` của wave hiện tại, dev/test-plan code + sinh test cho feature chưa tới lượt). Boundary chỉ sống **đúng 1 wave** thì bỏ trống field này — `features[]` phẳng đã đủ, không cần khai.
   - `ref_skills[]` = **situational ref skill** boundary cần (ngoài scaffold pattern/config/logging tự động) — suy từ design step 3: boundary **phát/nhận event** (có `events/{boundary}-events.md`) → thêm ref event; **dùng cache/lock** → ref cache; nhu cầu khác (search, grpc…) → ref tương ứng. Tra tên skill có sẵn ở `.claude/skills/ref-{kind}-*`. Để rỗng `[]` nếu chỉ CRUD thuần. *(Đây là nơi DUY NHẤT quyết ref per-boundary → materialize vào dev agent + build_prompt.)*
4. **KG skeleton per boundary** — `knowledge-base/{boundary}.knowledge-graph.yaml` (chỉ `metadata`; các section còn RỖNG). **KHÔNG điền entities/business_rules/events ở đây** — docs còn sửa qua `/domain`. Phần design được **seed ở `/run-wave`** từ docs cuối (sau approve); phần kinh nghiệm do dev/fix/review append.

> **MATRIX là kernel file** (PreToolUse chặn Write/Edit tay) — KHÔNG ghi bằng Write tool. Materialize qua script:
> ```bash
> py scripts/materialize_matrix.py <boundaries.json>     # hoặc --json '[...]' ; --mode merge ; --dry-run
> ```
> Script gate `stage ∈ {BOOTSTRAP, PLAN}`, validate (kind hợp lệ, boundary_id unique, depends_on tồn tại) rồi ghi MATRIX + bump revision.

## Phương pháp chia wave
1. **Map FEAT → boundary**: từ charter boundaries (Discovery D3) + FEAT/`epic_ref` (DOMAIN) + decomposition (DESIGN).
2. **Dựng đồ thị phụ thuộc** boundary/FEAT (`depends_on`): cái gì cần cái gì ready trước.
3. **Topological → wave** (sprint):
   - **Wave 1 = foundation mỏng** (auth/shared + 1–2 capability core) đủ chạy **E2E sớm** (login + 1 luồng nghiệp vụ chính).
   - **Wave kế** = boundary/FEAT phụ thuộc wave trước, nhóm theo lát giá trị ship được cùng nhau; ghi rõ `dependencies` từ wave trước.
   - **Kích thước wave: đếm tổng AC của mọi FEAT trong wave — chia nhỏ để dễ triển khai.** Ngưỡng là **`ac_cap_per_wave` khai ở frontmatter `WAVE-SEQUENCE.md`** (không khai → mặc định **6**). Chọn theo quy mô: project vừa để 6; project lớn vài trăm AC để 10-15 — vì mỗi wave là một vòng đầy đủ dev → review 2 lượt → dựng Docker → sinh test → chạy test → dogfood 6 vai × 2 đợt, nên ngưỡng quá nhỏ ở project lớn đẻ ra hàng chục wave mà chi phí vận hành nuốt hết thời gian làm việc thật.
     - **Ngưỡng là KHUYẾN KHÍCH, luồng mới là luật.** Chia nhỏ theo ngưỡng thì dễ triển khai; nhưng tách ra mà **đứt luồng** (nửa luồng ở wave này, nửa kia ở wave sau, không demo được luồng nào trọn) thì **giữ tròn luồng**, vượt ngưỡng cũng được.
     - Gate `wave_sequence_lint` (đếm heading `### AC-n` trong từng FEAT file): vượt ngưỡng **mà không nói lý do** → chặn. Điền `rationale` (≥20 ký tự) trong YAML block của wave nói **luồng nào sẽ đứt nếu tách** → cho qua, chỉ cảnh báo. Vượt hơn 2× ngưỡng vẫn cho qua nếu có lý do, nhưng cảnh báo mạnh hơn — cỡ đó thường là nhiều luồng gộp lại, rà xem tách theo luồng được không.
     - "Nhét cho gọn số wave" KHÔNG phải lý do — đó không phải đứt luồng. Wave nhiều AC là wave dev làm nửa chừng dễ bỏ sót, review khó soi hết, dogfood khó phủ. Ít AC quá (1-2) không cần tách.
   - Lặp tới khi **mọi** boundary/FEAT đã vào 1 wave.
4. **Viết wave-{N}.md cho mọi wave** (theo `TEMPLATE.wave.md`).
5. **Materialize MATRIX** (mỗi boundary: `wave` + `features[]` + `ref_skills[]` + `depends_on`) + **KG skeleton** per boundary.

## Chia lại sau khi đã chạy wave

Kế hoạch không cố định từ đầu. Chạy xong wave k (`/next-wave` đã lưu `archive/wave-k/`) mà phát hiện thiếu tài liệu → quay lại `/domain` bổ sung, rồi tới chốt này **chia lại**. Nhận biết: có thư mục `archive/wave-*`. Wave kế = wave đóng gần nhất + 1.

**Phần bù CHEN VÀO NGAY WAVE KẾ, tính năng đã xếp LÙI DẦN ra sau.** Không gom phần bù thành một wave để cuối cùng mới làm — các wave ở giữa sẽ xây trên nền đang thiếu, luồng đứt.

```
Kế hoạch cũ          Sau khi chia lại (vừa đóng wave 2, phát hiện thiếu X)
wave 3: A, B, C      wave 3: X, A, B     ← X chen vào wave kế
wave 4: D, E         wave 4: C, D        ← C bị đẩy xuống
                     wave 5: E           ← tràn qua wave cuối → sinh wave mới
```

1. **Wave đã đóng bất biến** — không đổi FEAT của wave ≤ k trong MATRIX/WAVE-SEQUENCE. Cần sửa thứ đã giao → đó là phần bù, đưa vào wave kế (FEAT mới, hoặc thêm AC vào FEAT cũ rồi xếp FEAT đó vào wave kế).
2. **Phần bù** = FEAT mới + FEAT đã giao có AC mới → đặt ở **wave k+1**. Chỉ đặt xa hơn khi có lý do thật (vd phụ thuộc thứ chưa làm) — ghi trong block §wave của WAVE-SEQUENCE:
   ```yaml
   placement_rationale:
     FEAT-hrm-044: "cần FEAT-hrm-031 (bảng lương) giao ở wave 4 mới tính được"
   ```
3. **Đẩy lùi giữ luật chia wave** — thứ tự phụ thuộc, ngưỡng AC (khuyến khích; tròn luồng thắng con số). Tràn → thêm wave mới ở cuối (WAVE-SEQUENCE + `wave-{N}.md` + `features_by_wave`).
4. **Không rơi mất** — mọi FEAT đã xếp cho wave sau trong kế hoạch cũ phải còn chỗ trong kế hoạch mới, hoặc ghi `status: deferred|dropped` ở FEAT kèm lý do. Nguồn phần bù cần quét: dòng `wave sau` ở `tracking/wave-*/dogfood-report.md`, `tracking/blockers.md`, và chỗ thiếu người vận hành báo.

Gate `replan_integrity` (chốt chia-wave) kiểm cả ba luật 1, 2, 4 bằng cách so MATRIX sống với MATRIX trong `archive/`. Xong chốt này → `/approve-document` lại (gate `replan_approved` chặn `start-wave` tới khi duyệt) → `/run-wave` chạy wave kế theo kế hoạch mới.

## Flow (/domain)
- Iterate với user: trình bày WAVE-SEQUENCE (toàn dự án) + tất cả wave-{N}.md + MATRIX → "OK chưa? chỉnh gì?" → sửa. Lặp tới khi user confirm (không giới hạn số vòng).
- Sau user confirm: return RETURN SCHEMA với `user_confirmed: true` → main chạy `py scripts/harness.py plan complete '{}'` (gate plan_gate: WAVE-SEQUENCE + MATRIX + wave files + KG) → transition PLAN → REVIEW.

## Quality checklist
- [ ] WAVE-SEQUENCE phủ **100% boundary + FEAT** (không sót, KHÔNG gom hết vào 1 wave). **Gate `plan_integrity` enforce chiều ngược:** FEAT-*.md không nằm trong `features[]` boundary nào = MỒ CÔI = chặn (chủ động hoãn/bỏ → frontmatter `status: deferred|dropped`).
- [ ] **Contract graph khớp MATRIX (gate `contract_graph_parity`):** `depends_on`/`consumed_by` trong MATRIX khớp 2 chiều với api-*.md `consumers[]` + INTEG-INT consumer/producer + events subscribers — cạnh gọi nhau phải có contract doc ghi nhận, contract không được khai cạnh MATRIX không có.
- [ ] **No orphan capability** — mỗi wave cover ≥1 capability từ CHARTER §3; mọi capability có wave (ZIP planning-rules).
- [ ] Chia **≥ 2 wave** khi có phụ thuộc; thứ tự topological (không phụ thuộc ngược/vòng).
- [ ] **Mỗi wave trong WAVE-SEQUENCE có file `wave-{N}.md` detail tương ứng** (full plan).
- [ ] Mỗi wave có goal + boundaries + features + **dependencies từ wave trước** + exit criteria.
- [ ] **MỌI wave điền đủ `wave_class` + `wave_strategy` + `targets` + §2 block YAML** (gate `wave_sequence_lint` parse: enum + `target_count_per_layer ≤ 3` + strategy layer-purity + vertical `parent_epic` + `inherited_active` file tồn tại — sai field này chặn `/domain`).
- [ ] Wave 1 mỏng, chạy được **E2E** (foundation + 1 lát core).
- [ ] Mỗi wave trong ngưỡng `ac_cap_per_wave` (tổng AC mọi FEAT trong wave). Vượt vì tách ra thì đứt luồng → điền `rationale` nói luồng nào đứt; vượt không lý do thì gate `wave_sequence_lint` chặn.
- [ ] Chia lại sau khi đã đóng wave (có `archive/wave-*`): wave đã đóng không đổi · phần bù ở wave kế (hoặc có `placement_rationale`) · không FEAT nào rơi mất (gate `replan_integrity`).
- [ ] **Deferred-scope khai báo tường minh**: AC/feature chủ động hoãn sang wave sau (auth/idempotency/event ở wave CRUD…) ghi vào `## 6 → Deferred to later waves` của `wave-{N}.md` (token `FEAT-NNN[:AC-M]`/`BR-NNN`). Đây là SoT để test-plan tag `@deferred` → test-execute skip → end-wave close sạch (không cần ép `test_result`).
- [ ] MATRIX mỗi boundary đủ `kind/prefix/tech/wave/features/depends_on`; `ref_skills[]` suy từ design (event/cache/extra → ref tương ứng; CRUD thuần để rỗng); KG skeleton mọi boundary.
- [ ] **Không có `TBD` / section trống mơ hồ** — chỗ chưa chốt ghi `Open question` (cần ai quyết + vì sao).

## Done
- WAVE-SEQUENCE + **wave-{N}.md cho mọi wave** + MATRIX (≥1 boundary) + KG skeleton (khớp gate plan_gate); user đã confirm → PLAN → REVIEW (rồi /approve-document → /run-wave).
