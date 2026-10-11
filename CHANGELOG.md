# Changelog

## 0.1.0 — initial release candidate

- AirPlay audio discovery and one- or multi-speaker selection in the Omarchy Audio menu.
- Native AirPlay 2 sender integration and shared timing for multiroom playback.
- Independent selected-speaker sliders, average-based Sync Volume, and correct master output volume/mute.
- Audio-specific AirPlay icons and Omarchy theme styling.
- Explicit setup with pinned sender checksums, narrowly scoped timing rules, and dependency cleanup.
- Plugin-owned worker lifecycle, portable XDG paths, and isolated regression tests.

The original setup was confirmed with two HomePods. Clean-install and additional receiver testing remain before a stable compatibility claim. This initial release does not support PIN/password pairing or IPv6-only discovery.
