# Architecture

JP-Bench is a small Python package with one job: turn a browser agent's output on a Japanese government task into a pass, fail, or safety violation.

```
tasks/*.yaml --> task.py (load, validate) --> prompt.py (render, hash)
                                              |
                       adapters.py / runner.py (call a model, record raw output)
                                              |
                       parse.py (strip reasoning, extract JSON, classify answer)
                                              |
                       scoring.py (compare to gold, using normalize.py rules)
                                              |
                       cli.py (list, show, validate, prompt, score, run, report, doctor)
```

## Modules

| module | role |
|---|---|
| `task.py` | Task dataclass, schema rules, loader. Rejects unsafe or inconsistent tasks before anything runs. |
| `normalize.py` | Notation rules: width, entity suffixes, dates in era notation, numbers with 万 and 億, URLs, statute references, identifiers, addresses. |
| `scoring.py` | One scorer per success type, a registry, and aggregate summaries with Wilson intervals. Safety violations score zero. |
| `prompt.py` | Renders a task as a prompt in Japanese or English. Stable hash and length limit. |
| `parse.py` | Turns raw output into JSON. Refusals, empty output, and invalid output are classified, not raised. |
| `adapters.py` | Model interface. Offline adapters for tests and replay. HTTP adapters read keys from the environment only. |
| `runner.py` | Runs tasks through an adapter, retries adapter errors, records one result per task, writes results atomically. |
| `cost.py` | Validated price table and cost estimates. |
| `cli.py` | Command-line entry points. |

## Design rules

- Scoring is deterministic and offline. No scorer calls a network service.
- A safety violation (submitting a form that must stop before submit) overrides every other result.
- Results and metadata never contain API keys.
- Gold answers come from official sources at evaluation time; the repository holds only fictional inputs for form tasks.
