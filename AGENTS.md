# Repository maintenance

For end-user installation, use [INSTALL.md](INSTALL.md). An installation-only task
does not require this repository maintenance workflow or the runtime skill instructions.

This file guides agents maintaining the repository. The product's runtime entry is
`skill/zuihan-kanshu/SKILL.md`; its mathematical roles live in that skill's references.

## Source and scope

- Edit the single runtime source under `skill/zuihan-kanshu/`. Build packages with
  `tools/build_release.py`; do not edit generated `dist/` copies.
- `VERSION` owns the version. Keep the skill title, versioned command-line scripts,
  manifest, tests, and release notes consistent when changing it.
- Keep public documentation, examples, and contributor instructions in the repository,
  outside the runtime package. A built-in guide needed to answer usage questions may
  live as a runtime reference and be linked directly from the public homepage; maintain
  one guide source rather than a separate public copy. Use synthetic or already public examples. Personal
  research, private maintenance records, host paths, and conversation identifiers do
  not belong in this public tree.
- Preserve historical names where they describe a historical fact. Current paths and
  invocation examples use `zuihan-kanshu`. Avoid duplicate compatibility skills.
- Keep mathematics, provenance, and implementation claims accurate. A successful
  structural check or calculation does not prove a mathematical claim.

## Working with agents

Follow the current user's scope and the host's actual tools and permissions. When
delegation is available and permitted, prefer a capable execution agent for substantive
implementation, including tightly coupled tasks. The coordinator owns requirements,
important decisions, integration, and final acceptance. The maintenance preference is
`gpt-6.1-sol` with `max` effort for execution; use supported alternatives when necessary
and report material limitations accurately.

Give each shared write area one owner. Parallelize independent work only. Use fresh,
task-specific contexts for independent reviews. An execution agent may delegate one
further level when useful and permitted; those leaf agents do not delegate again.
Review the delivered changes and relevant evidence, reuse valid checks, and send concrete
defects back to the responsible author. Do not add fixed review rounds or require the
user to reconfirm work already authorized.

## Validation and delivery

Read `CONTRIBUTING.md` for commands and the distinction between lightweight checks and
PDF integration tests. Verify behavior affected by the change and state which checks
actually ran. Report missing tools and skipped tests without treating them as passes.
Keep generated caches, build output, and temporary evidence out of commits.

Repository publication, package submission, merging, and installed-plugin updates are
separate actions. Carry out the actions authorized in the current task; preparation or
a successful build alone does not establish authorization for another action.

