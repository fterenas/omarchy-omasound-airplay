# Release validation

Local packaging checks completed on 2026-10-11:

- 16 isolated tests passed: AirPlay discovery/merging, selection, independent and average-linked volumes, master metadata handling, and worker exit after abrupt wrapper termination.
- Python sources compiled successfully.
- `omarchy plugin validate` accepted the manifest and entry points.
- `Panel.qml` and `Service.qml` both reached Qt Component.Ready using the installed Quickshell and Omarchy UI modules.
- Upstream v0.5.5 binary checksums and tagged license/notice links were verified.

The prototype's two-HomePod audio playback was confirmed by the user earlier in the development session. These checks do not replace a clean-install test of the packaged first-run installer on another machine. No privileged setup was executed from the release package, and the existing working desktop configuration was not switched to the new plugin during packaging.
