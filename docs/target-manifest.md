# Target Adapter Manifest

Target Lab can register and analyze local repositories or GitHub repositories.

Capability discovery is heuristic. Active target tests require an explicit adapter manifest in the target repository:

```text
.aasl/target.json
```

## Why an explicit manifest

AASL does not automatically execute arbitrary repository code.

The manifest is an explicit trust decision by the repository owner. Only commands listed in the manifest are eligible for Target Lab execution.

Commands:

- run without a shell;
- run from the repository root;
- have a 120-second timeout;
- receive only a minimal environment;
- must emit one JSON result to stdout.

## Example

```json
{
  "version": 1,
  "commands": {
    "lab01": [
      "python",
      "security/aasl/lab01_target.py",
      "--mode",
      "{mode}"
    ],
    "lab02": [
      "python",
      "security/aasl/lab02_target.py",
      "--mode",
      "{mode}"
    ]
  }
}
```

The literal `{mode}` token is replaced with the scenario selected in the UI.

## Result contract

A target adapter must output one JSON object containing at least:

```json
{
  "finding": false,
  "verdict": "pass",
  "severity": "none"
}
```

Adapters may add any additional evidence required by the lab.

## Recommended repository layout

```text
your-repo/
├── .aasl/
│   └── target.json
└── security/
    └── aasl/
        ├── lab01_target.py
        ├── lab02_target.py
        └── README.md
```

Use **Create Adapter Scaffold** in Target Lab to create the directories and an empty manifest.

## GitHub targets

A GitHub URL can be registered directly.

Target Lab can shallow-clone it into the AASL state directory for analysis. Cloning does not execute target code.

Active target execution still requires an explicit adapter manifest.

## Safety

Only run adapters for repositories you trust and systems you are authorized to test.

Prefer:

- local/test environments;
- synthetic identities;
- benign canaries;
- test credentials;
- disposable resources;
- dry-run or simulated privileged actions.
