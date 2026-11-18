# Mullet for Hermes installed

Enable it if you did not install with `--enable`:

```bash
hermes plugins enable mullet
```

Restart Hermes or the gateway after enabling.

In shared gateways, restrict `/mullet` to trusted users with Hermes slash-command access controls; runtime mode is process-local.

Commands:

- `/mullet [lite|full|ultra|off]`
- `/mullet-review [target]`
- `/mullet-audit [target]`
- `/mullet-debt`
- `/mullet-gain`
- `/mullet-help`

Bundled skills are available as `mullet:mullet`, `mullet:mullet-review`, `mullet:mullet-audit`, `mullet:mullet-debt`, `mullet:mullet-gain`, and `mullet:mullet-help`.

For perpetual local expansion invoke `/mulletize`. Each worktree keeps its own ledger.
