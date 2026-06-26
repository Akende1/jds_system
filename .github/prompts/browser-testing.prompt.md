---
description: "Test a web app in the browser and report UI or behavior issues"
argument-hint: "Page, flow, or feature to verify; expected behavior; device or browser"
agent: "agent"
---
Test the requested page, flow, or feature in the browser.

Use the provided arguments and any relevant workspace context to drive the test. Focus on observable behavior only.

What to check:
- Open the target page or flow and complete the main happy path.
- Verify navigation, forms, buttons, loading states, errors, and visible data.
- Check the layout on desktop and, if relevant, mobile-sized viewports.
- Reproduce any failures with the smallest possible set of steps.
- If a bug is found, note the exact user action that triggered it and what should have happened instead.

Report the results in this format:
- Summary: one short paragraph
- Passed checks: brief bullets
- Issues found: severity, location, repro steps, expected result, actual result
- Notes: any constraints, uncertainties, or follow-up checks

Keep the response concise, factual, and actionable.