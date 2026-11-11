# Portable VM Labs

AASL can materialize disposable Linux guests for Career Lab exercises that benefit from a real host environment.

## Portability model

Git stores the **blueprint**, not the VM disk.

```text
Git repository
  └── lab.json
  └── cloud-init.yaml
  └── synthetic artifacts
          |
          v
      Multipass
          |
   host virtualization
          |
          v
   fresh Ubuntu guest
```

No `.qcow2`, `.vhdx`, `.utm`, or other large VM disk image is committed to Git.

## Host support

The AASL runtime uses Multipass because the same CLI workflow is available on:

- Linux;
- macOS;
- Windows.

The virtualization backend is selected by Multipass for the host.

## Current blueprints

### linux-soc-dfir

For:

- SOC analysis;
- threat hunting;
- DFIR;
- malware/sandbox interpretation;
- detection engineering.

### linux-appsec

For:

- AppSec code review;
- synthetic authorization bypass analysis;
- sensitive-data / secret discovery.

### linux-cloud-iam

For:

- IAM policy review;
- agentic trust-boundary analysis;
- AI-agent authorization traces;
- crypto configuration review;
- governance / SOAR design support.

## Start from the website

When Multipass is installed, a VM-backed Career scenario shows:

- Start VM
- Reset VM
- Stop VM
- the shell command for the guest

Example:

```text
multipass shell aasl-linux-appsec
```

## Reset semantics

Portable correctness does not depend on snapshots. The portable reset model is **destroy and recreate from the Git blueprint**.

**Reset VM**:

1. deletes the selected AASL instance with per-instance purge;
2. launches the guest again from the version-controlled blueprint;
3. reapplies cloud-init.

This produces the same clean lab state across supported host families.

## Why not store prebuilt VM disks

Large disk images in Git would be:

- architecture-dependent;
- slow to clone;
- difficult to review;
- difficult to version meaningfully;
- likely to require Git LFS;
- less reproducible than text-based provisioning.

Blueprints keep the exercise inspectable and portable.

## Safety

VM artifacts are synthetic.

The current guests do not contain real credentials, destructive malware, or external-target exploit instructions.

VM-backed exercises should remain isolated and disposable. Future scenarios that require networking should define explicit network policy in the blueprint rather than inheriting unrestricted access by default.


## Scaling beyond local Multipass

Local Multipass is the individual learner runtime. For concurrent hosted labs, browser-only learners, Windows/AD environments, or multi-machine ranges, use a cloud sandbox provider rather than scaling local Multipass.

See [Cloud Scaling for VM-Backed Labs](cloud-lab-scaling.md).
