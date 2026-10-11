# Third-party notices

## Omarchy

`Panel.qml` and `Model.js` derive from Omarchy's Audio widget. Copyright (c) David Heinemeier Hansson. Used and modified under the MIT license included in `LICENSE`.

Upstream: https://github.com/omacom/omarchy

## cliairplay / Music Assistant AirPlay CLI

The setup helper downloads the upstream Linux release **v0.5.5**. The executable is not bundled in this repository or its source release. The combined sender includes GPLv3-licensed components and additional upstream notices; our MIT license does not relicense it.

- Release and binaries: https://github.com/music-assistant/airplay-cli/releases/tag/v0.5.5
- Corresponding source: https://github.com/music-assistant/airplay-cli/tree/v0.5.5
- License: https://github.com/music-assistant/airplay-cli/blob/v0.5.5/LICENSE
- Upstream dependency notices: https://github.com/music-assistant/airplay-cli/blob/v0.5.5/THIRD_PARTY_NOTICES.md

Obtain source using the upstream recursive-clone instructions to include its submodules. OmaSound makes no changes to the downloaded sender.

## Original troubleshooting reference

The development session began with https://github.com/ETroll/omarchy-airplay, which provided the screen-mirroring starting point. OmaSound's audio backend is independently implemented around Music Assistant's sender; it does not package DoubleTake or the original screen-mirroring plugin.

AirPlay is an Apple trademark. OmaSound is an independent community project and is not affiliated with Apple or the Omarchy maintainers.
