# Comptroller's comparison lab

**Offline acceptance.** Run `python3 tests/ratification.py` for FizzBuzz, Todo and the 46-input charter. Run `python3 tests/mulletize.py` for the recurring supervisor. The example line-count command in the root README counts physical source, including generated statute books.

**Single-shot comparison.** From the repo root, run `npx promptfoo eval -c benchmarks/promptfooconfig.yaml`. The same tasks go to baseline, Caveman and Mullet. Choose a provider/model and credentials in your own environment. Promptfoo reports token use and provider cost where available. The LOC scorer counts nonblank, noncomment response code. The third arm reads an installed JuliusBrussee/caveman skill from ~/.agents/skills/caveman/SKILL.md. Set CAVEMAN_SKILL to use a different installed path.

**Agentic comparison.** With a Claude Code CLI that supports plugin evals, run `claude plugin eval . --no-publish --json report.json`. The cases in `evals/` ask agents to build a working sorter and a UTF-8 ticket office. The graders score correctness, exercised institutions and receipts. Use the same model and trial count for both arms. Review the generated workspace and the per-case outputs before reporting growth. Live evaluations use your configured provider. This repository ships the tasks and graders; it makes no model-performance claims.
