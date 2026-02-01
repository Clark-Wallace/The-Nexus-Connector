# Archive Contents

This directory contains archived items that are not part of the active development but may have reference or historical value.

## Directory Structure

### `/spinoff-projects/`
Contains standalone projects that branched from Nexus but are now separate efforts.

- **QwenDevr/** - Claude Code-inspired CLI development assistant powered by Qwen models via OpenRouter. This is a complete standalone tool with its own setup, requirements, and documentation. Could be extracted as its own repo.

### `/future-concepts/`
Contains design documentation and specifications for features not yet implemented.

- **UAP/** - Universal Agent Protocol Framework documentation. An ambitious multi-agent orchestration system with features like intelligent task routing, workflow orchestration, enterprise monitoring, and visual dashboards. References packages (`uap_core`, `uap_orchestration`) that don't exist yet. Good reference for Phase 5-7 of the development roadmap (MCP Support, Smart Routing, Production Hardening).

### `/superseded-docs/`
Contains documentation that has been replaced by newer versions.

- **NEXUS_DEVELOPMENT_ROADMAP.md** - Original development roadmap, superseded by `.agent-os/product/roadmap.md`
- **PROJECT_STATUS.md** - Original project status, superseded by plan mode documentation

### `/build-artifacts/`
Contains build outputs that can be safely regenerated.

- **dist/** - Python distribution files (wheel, sdist)
- **nexus_connector.egg-info/** - Package metadata generated during install

### `/old-backups/`
Contains manual backups of the codebase.

- **The-Nexus-Connector backup/** - Manual backup of the entire project, likely created before major changes

## Recovery

To restore any archived item:
```bash
# Example: Restore QwenDevr to root
mv .archive/spinoff-projects/QwenDevr ./QwenDevr

# Example: Restore UAP docs
mv .archive/future-concepts/UAP ./docs/UAP
```

## Notes

- Build artifacts can be regenerated with `python -m build`
- The .archive folder is gitignored - consider whether to track these items
- Review before permanent deletion to ensure no valuable content is lost
