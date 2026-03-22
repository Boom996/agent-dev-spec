---
name: competitive-plan-validator
description: Combine current external competitor research with internal scenario simulation to evaluate a product plan, expand differentiators, and turn competitor weaknesses into concrete product improvements. Use when a user asks for competitor analysis, market comparison, positioning pressure tests, or wants to upgrade a PRD, framework, roadmap, strategy memo, or product concept against current products.
---

# Competitive Plan Validator

Use this skill when the task is not only "does this product plan work", but also "how does it compare with the current market, what strengths should we claim more clearly, and what competitor tradeoffs should we turn into roadmap moves".

This skill combines two lenses:

- internal simulation: pressure-test the plan in realistic workflows, especially human plus agent collaboration
- external comparison: search current competitors and adjacent products, extract validated capabilities, then convert their gaps and strengths into concrete changes for your product

Load [references/competitor-lenses.md](references/competitor-lenses.md) when choosing competitor buckets and comparison dimensions.  
Load [references/deliverables.md](references/deliverables.md) when structuring outputs, naming files, and deciding how much evidence to include.

## Required outputs

Produce three separate markdown files for each analysis wave:

- a `...竞品扫描记录.md` file with the search scope, selected competitors, evidence notes, and immediate observations
- a `...竞品分析报告.md` file with the synthesis: market position, expanded strengths, weaknesses, and competitor-informed recommendations
- a `...产品增强建议.md` file with the concrete backlog or framework changes to make next

Default to one triplet per product concept. Split into multiple triplets only when the product has clearly different markets, buyers, or workflows.

## Workflow

### 1. Ground in the plan

Read the plan and extract:

- target user or buyer
- core promise
- workflow the product wants to improve
- required system behaviors
- explicit constraints
- claimed differentiation

If key details are missing, infer the smallest useful assumption set and state it in the outputs.

### 2. Choose competitor buckets before brand names

Do not jump straight to famous companies. First define 2 to 4 buckets such as:

- direct competitors
- adjacent workflow products
- substitute tools or platforms
- governance or observability overlays

Then pick the smallest competitor set that can expose:

- where the market is already strong
- where your product is genuinely different
- what users may expect as table stakes soon
- what gaps become obvious once compared

### 3. Browse current external sources

This skill requires browsing current sources. Prefer:

- official product docs
- official product pages
- official release notes
- official pricing or enterprise feature pages
- official GitHub repos when the product is open source

Use specific absolute dates in notes and reports. When a point is inferred rather than directly stated by the source, label it as an inference.

### 4. Build a competitor matrix

Compare competitors using the dimensions in [references/competitor-lenses.md](references/competitor-lenses.md). At minimum, cover:

- target workflow
- execution model
- state and memory
- coordination or handoff model
- governance and permissions
- observability and replay
- portability and lock-in
- adoption friction

Do not reward breadth blindly. Prefer the few dimensions that materially change buyer judgment.

### 5. Reverse the comparison into product advantage

After the scan, answer:

- which competitor strengths actually validate the market
- which competitor tradeoffs make your product look better
- which claims your product can now state more clearly
- which missing capabilities users will soon expect from you

Separate:

- validated advantage your product already has
- advantage your product could claim only after more work

### 6. Turn competitor weaknesses into roadmap improvements

For each important competitor, identify:

- what they do well
- what they likely sacrifice or make heavier
- what part is worth borrowing
- how to adapt it without losing your product's shape

Favor product-shape changes over feature wishlists when repeated patterns point the same way.

### 7. If the product involves agents, run a human plus agent check

When the plan includes AI collaboration, automation, orchestration, copilots, or agent teams, also inspect:

- authorship and approval
- context access and scope control
- traceability of outputs
- review burden
- handoff freshness
- state drift across tools or sessions

## Output rules

- Keep the three files separate.
- Put assumptions in every file when they materially affect the result.
- Lead the report with the current market verdict.
- Include source links in the report.
- Use absolute dates such as `2026-03-21`.
- Distinguish facts from inference.
- Prefer concrete tradeoffs over generic praise.
- If the user already has an internal simulation report, synthesize it instead of repeating the same simulation.
- If competitor findings point to multiple product lines, keep one report per line instead of mixing them.

## File creation

Use `scripts/init_competitive_validation_run.py` to scaffold a new analysis set when helpful.

Example:

```bash
python3 scripts/init_competitive_validation_run.py "ADS竞品对标" --output-dir /path/to/output
```

This creates:

- `ADS竞品对标竞品扫描记录.md`
- `ADS竞品对标竞品分析报告.md`
- `ADS竞品对标产品增强建议.md`

Fill those files with the scan log, synthesis, and implementation suggestions.

Recommended arguments:

- `--source` for the plan path or source description
- `--date` when you need the scaffold files to match a specific research date
