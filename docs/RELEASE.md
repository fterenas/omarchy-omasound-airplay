# OmaSound AirPlay v0.1.0

Stream existing Omarchy application audio to one or more AirPlay speakers from the Audio menu.

This first release includes network discovery, speaker checkboxes, sliders for selected speakers, independent receiver volume, and Sync Volume. Sync Volume brings selected speakers to their average level and keeps them linked. Master volume and mute follow the active speaker or group. Audio-specific AirPlay icons and Omarchy theme styling complete the widget.

Setup is launched explicitly from Audio. It installs a verified cliairplay v0.5.5 sender with timing-port permission and requests narrow, receiver-specific UFW rules when needed. Disabling the plugin stops playback connections and restores local audio; optional dependency cleanup is included.

The original implementation was confirmed with two HomePods on OS 27. This is an early release: the portable installer needs testing on a second machine, and PIN/password pairing, IPv6-only discovery, and reliable mixed-generation groups are not supported. Discovery alone does not establish receiver compatibility.

Validation: 16 isolated regression tests passed; manifest validation passed; both QML entry points compiled against the installed Omarchy shell. Sender checksums were verified against the upstream v0.5.5 release.
