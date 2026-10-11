# Troubleshooting

## No speakers appear

Open **Audio → Set up / repair AirPlay** and complete setup. Wait 20 seconds. Keep the computer and speakers on the same local network; guest networks or wireless client isolation may block multicast discovery. IPv6-only receivers are not supported.

From the installed plugin directory, `python3 bin/setup.py --check` reports missing prerequisites, checksum problems, or timing-port permission problems. `avahi-browse -rt _airplay._tcp` and `avahi-browse -rt _raop._tcp` can diagnose discovery. These are optional troubleshooting commands, not part of normal listening.

## A checked speaker stays silent

Start playback in your app and check that the desired speaker has a nonzero slider. Wait up to 35 seconds for a group to connect. Respond to any UFW administrator prompt. A startup failure should produce a notification and return playback to a physical output; selecting the speaker again retries.

For the initial release, test HomePods individually before creating a group. A device appearing in discovery may still require unsupported PIN or password pairing. Avoid mixing receivers with different timing protocols. An existing sender or a development `airplay-audio.service` may already own the timing ports; stop it before using OmaSound.

If your firewall was reset after a successful connection, OmaSound's saved firewall receipt may no longer reflect the active rule. Restore the narrow rule for that receiver through your firewall settings. Do not disable your firewall wholesale. The receipt files live in your OmaSound state directory.

## Master volume is zero or shows a muted icon

Ensure only one audio-widget clone is enabled and that OmaSound owns the selected output. A group with all speaker levels at zero should show zero/muted. The package keeps the hidden group bound to the PipeWire tracker and mirrors actual receiver levels, including hardware volume-key changes. If a previous QML version is cached, `omarchy restart shell` reloads it (this reconnects OmaSound playback).

## Report a problem

Include the Omarchy version, OmaSound version, computer architecture, receiver model/OS version, whether individual playback works, and the setup-check result. Review logs before posting: sender debug output can contain local addresses and receiver names. Never include credentials or pairing secrets. UI compatibility can change as Omarchy evolves; report the installed Omarchy version rather than assuming all shell versions behave alike.
