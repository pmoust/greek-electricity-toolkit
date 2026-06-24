# Weekly offer-refresh brief (for the agent)

You are refreshing `data/offers_current.json` for the greek-electricity-toolkit.
**Read and follow** `.claude/skills/greek-electricity-bill-analysis/SKILL.md` and
`greek-tariff-reference.md` — they define the method and the supplier list.

## Do this

1. Pull the **current active residential + small-business supplier list** from the
   official ΡΑΑΕΥ tool **energycost.gr** (and pricefox.gr / provider pages as backup).
2. For each supplier already in `data/offers_current.json`, and any **new entrant**
   you find, get each flagship product's current values: effective €/kWh (after the
   on-time / direct-debit discount), πάγιο, RAAEY color, tariff type, contract term,
   whether it has an adjustment clause, segment (resi / resi-night / business).
3. For tiered or formula-indexed (a×DAM+b, hourly MCP) products, reduce to an
   **effective** €/kWh at a typical consumption / the current wholesale index, and
   say so in the product note.
4. Update `data/offers_current.json` in place. **Every offer must keep a `source`
   URL and an `date` (access date).** Set `meta.last_verified` to today.

## Rules (non-negotiable)

- **Never invent a rate.** If you can't source a value, drop the offer and note it
  in the PR body — do not guess.
- **Completeness:** the refreshed list must still contain every previously-active
  supplier, OR the PR body must explain each removal (merged / exited / went
  direct-only). Account for consolidation (e.g. WATT+VOLT→Protergia, Elpedison→
  Enerwave, Volterra→Metlen).
- **Don't rank across commitment tiers** or assert a single "cheapest" — that's the
  human's call. Just refresh the data.
- Keep the JSON schema exactly as the existing file (the validator enforces it).

## Output

Write only `data/offers_current.json`. The workflow validates it and opens a PR for
human review — it is never auto-merged. Summarise what changed (rate moves, new /
withdrawn products, mergers, regulated-rate or VAT/ΕΦΚ changes) for the PR body.
