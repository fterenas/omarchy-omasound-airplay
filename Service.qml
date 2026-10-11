import QtQuick
import Quickshell.Io

Item {
  property var shell: null
  readonly property string runner: decodeURIComponent(Qt.resolvedUrl("bin/runner.py").toString().replace(/^file:\/\//, ""))
  Process {
    id: backend
    command: ["/usr/bin/python3", runner]
    // The open pipe is our lifetime token. Closing it stops the worker and senders.
    stdinEnabled: true
    running: true
  }
  Timer {
    interval: 10000
    running: true
    repeat: true
    onTriggered: if (!backend.running) backend.running = true
  }
  Component.onDestruction: backend.stdinEnabled = false
}
