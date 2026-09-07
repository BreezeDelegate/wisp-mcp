# Wisp MCP public onboarding design

## Mode

Replace / clean slate. The previous public landing hierarchy, hero, cards, marketing sections, visual motifs and CSS are anti-references and have no design authority.

## Product job

A first-time user should arrive on `wisp.hinoake.com` directly on the ChatGPT readiness step of a guided setup that takes them from ChatGPT readiness to a verified read-only WISP connection.

## Non-goals

- no marketing landing page before onboarding;
- no feature/capability/security/FAQ sections around the flow;
- no product-tour cards or screenshot gallery;
- no reuse of the rejected hero, section hierarchy, card grammar, palette or layout;
- no request for WISP/OpenAI secrets in the browser.

## Journey

1. ChatGPT: identify whether the current plan supports full MCP and recommend the strongest model available.
2. GitHub: connect GitHub and prepare a private project repository for durable rules/roadmap/handoff.
3. WISP: confirm the panel and Client API token location.
4. VPS: confirm a supported Linux machine and SSH access.
5. Install: run the one-line installer and require `Wisp API: OK` before continuing.
6. Connect ChatGPT: configure Secure MCP Tunnel and confirm Wisp tools are visible.
7. Project memory: offer three optional Skill-creation instructions for project memory, safe Wisp operations and release verification.
8. Done: issue one read-only validation prompt.

## Composition

Desktop uses a persistent setup rail and one focused stage. Mobile replaces the rail with a compact sticky progress header. Only one onboarding step is rendered as active at a time. The page owns vertical scrolling; there are no horizontal content rails.

## Visual system

- warm paper canvas plus dark setup rail;
- coral action accent used only for current state and primary actions;
- no gradients, glass, glow, decorative dashboards or marketing imagery;
- typography and whitespace carry hierarchy before borders;
- plain text and meaningful step numbers replace decorative icons where icons are not required.

## Interaction contract

- state persists in browser localStorage only;
- URL hash represents the current visited step;
- Back/Continue always work by keyboard and touch;
- future steps cannot be jumped to until visited;
- language switching keeps the current step when possible;
- copy actions use a visible text button and accessible status message;
- required confirmations gate the next step but can be revisited.

## Acceptance gates

- root route is the onboarding itself, not a landing page;
- exactly eight onboarding steps in FR and EN;
- no old `hero`, `section-head`, `trustline`, `choice-band`, `faq`, `panel-proof`, or marketing-section structures in public pages/CSS;
- no `<section>` element in the root onboarding pages;
- 320/360/390/430, landscape phone, tablet and desktop have no horizontal overflow or clipped actions;
- 200% zoom remains functional;
- keyboard can complete the full flow;
- CSP permits only self-hosted script/style/assets and no network requests from onboarding JavaScript;
- HTML references CSS and JS with content-hash query keys; static QA rejects stale fingerprints and Nginx forces HTML revalidation;
- production promotion requires static checks, browser inspection, public smoke and rollback evidence.
