# Cloud Scaling for VM-Backed Labs

AASL uses local Multipass guests for individual development and learning. That is the right default because it is inexpensive, private, and cross-platform.

At larger concurrency, the VM control plane should move to cloud infrastructure.

## Stage 0 — local learner runtime

Use when:

- one learner owns the machine;
- exercises can use local CPU/RAM;
- no central scheduling is required;
- the learner can install Multipass.

Runtime:

~~~text
AASL UI
  -> local console
  -> Multipass
  -> disposable Ubuntu guest
~~~

Cost to the AASL operator: effectively zero cloud compute.

## Stage 1 — managed cloud sandboxes

Use when:

- many learners need simultaneous isolated Linux environments;
- browser-based access should work without local virtualization;
- guests need central lifecycle control;
- labs should start quickly and disappear automatically.

Recommended architecture:

~~~text
AASL web application
       |
       v
Sandbox Broker / Lab Scheduler
       |
       +-- identity / entitlement
       +-- concurrency quota
       +-- TTL / auto-destroy
       +-- image / blueprint selection
       +-- session ledger
       |
       v
Managed isolated sandbox
       |
       +-- learner terminal / HTTP endpoint
       +-- synthetic lab state
       +-- per-session credentials
~~~

### AWS Lambda MicroVMs

For disposable Linux/agent sandboxes, AWS Lambda MicroVMs are a strong future target.

They provide:

- Firecracker-backed VM isolation;
- managed lifecycle rather than operating the hypervisor fleet yourself;
- fast launch/resume;
- state preservation for bounded sessions;
- direct per-sandbox connectivity.

This is particularly relevant to AASL's future AI-agent and code-execution ranges.

Availability and regional constraints must be evaluated before production rollout.

## Stage 2 — EC2 / auto-scaled ranges

Use EC2 when labs need:

- Windows guests;
- Active Directory;
- custom kernels;
- privileged networking;
- multiple coordinated VMs;
- long-running state;
- packet capture / IDS appliances;
- complex VPC topologies.

A production design can combine:

- EC2 launch templates / AMIs;
- Auto Scaling;
- per-session security groups;
- short-lived IAM roles;
- Spot Instances for interruptible practice workloads;
- On-Demand Instances for non-interruptible assessments;
- automated TTL cleanup.

## Why not run raw Firecracker ourselves first?

Firecracker is excellent technology, but operating a secure multi-tenant Firecracker fleet means owning:

- KVM hosts;
- image lifecycle;
- networking;
- storage;
- scheduling;
- tenant isolation;
- jailer configuration;
- patching;
- observability;
- capacity management.

AASL should prefer managed primitives until scale or economics justify operating that infrastructure directly.

## Stage 3 — multi-machine enterprise ranges

For advanced red-team, SOC, DFIR, cloud, and identity exercises:

~~~text
Lab Session
  +-- attacker host
  +-- workstation
  +-- identity / directory host
  +-- application server
  +-- telemetry / SIEM
  +-- optional agent / LLM service
~~~

At that point AASL needs a real control plane with:

- session scheduling;
- network templates;
- image versioning;
- secrets injection;
- telemetry collection;
- scoring events;
- cost limits;
- inactivity timeout;
- automatic teardown.

## Cost controls from day one

Any cloud-backed AASL runtime should enforce:

- maximum concurrent sessions per user / organization;
- hard TTL on every environment;
- idle timeout;
- per-lab CPU/RAM ceilings;
- budget alarms;
- session-level cost attribution;
- automatic cleanup after browser disconnect / expiry;
- Spot usage where interruption is acceptable.

## Recommended AASL evolution

~~~text
Now
Local Multipass

Next
Cloud Sandbox Provider interface
  -> local Multipass provider
  -> AWS provider

Then
Linux managed microVM provider
+ EC2 provider for Windows / multi-host ranges

Later
multi-cloud provider interface if customer demand requires it
~~~

The key design requirement is that **lab definitions remain provider-neutral**. The Git blueprint should describe the desired exercise; the provider adapter decides how that exercise is materialized locally or in the cloud.