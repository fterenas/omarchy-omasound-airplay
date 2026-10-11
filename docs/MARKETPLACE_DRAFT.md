# Marketplace submission draft

Submit only after the public repository exists and the owner reviews the complete submission and required attestations.

Repository: https://github.com/fterenas/omarchy-omasound-airplay
Name: OmaSound AirPlay
Plugin ID: io.github.fterenas.omasound-airplay
Version: 0.1.0
Category: System
Tags: bar, media, quickshell

Description: Native AirPlay 2 audio for Omarchy—one speaker or multiple rooms, with independent and synchronized volume controls.

Install: Omarchy plugin manager, then Audio → Set up / repair AirPlay.
Permissions/setup: explicit first-run package installation and verified sender download; root-owned sender has timing-port binding permission; enabled UFW prompts for receiver-specific UDP 319–320 rules. Runtime audio runs as the user.
Removal: disabling stops connections and restores local output. Before removing the checkout, optional uninstall.py removes the dedicated sender and offers removal of rules OmaSound created. Shared packages and user settings are retained.
Compatibility: original implementation tested with two HomePods on OS 27; clean-install testing on a second machine and broader receiver testing remain. Initial release lacks PIN/password pairing and IPv6-only discovery.

Submission form: https://github.com/omacom/omarchy-plugin-marketplace/issues/new?template=submit-plugin.yml
Publishing guide: https://plugins.omarchy.org/publish.html

This file is a draft, not a submitted listing or a signed owner attestation.
