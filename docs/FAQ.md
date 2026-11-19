# FAQ

**Why do browser agents need this benchmark?**
Japanese administrative portals mix full-width and half-width characters, era dates, and abbreviated legal-entity names. An agent that copies the right value in a different notation should pass. An agent that copies the wrong value should fail.

**Why are gold answers not in the repository?**
Official sources change: registrations, subsidy calls, and statutes. Gold answers are fetched from official APIs or pages at evaluation time, and each task records its `gold_source` and `snapshot_date`.

**Why is form data fictional?**
Form tasks run up to a confirmation screen. Using fictional data means no real person or company is named in a filing, and the safety rule stops the agent before submission.

**What does a run cost?**
Costs depend on the model and the number of tasks. `jpbench run` does not call a model unless an adapter is chosen. The `cost` module estimates cost from a price table file you provide. Use `--dry-run` to see the prompts without any calls.

**Is the safety rule optional?**
No. A `form_fill` task must stop before submit. If an agent submits, the task scores zero with a SAFETY VIOLATION, whatever else it got right.

**Where do the sources come from?**
See [NOTICE.md](NOTICE.md). The repository does not redistribute their content.
