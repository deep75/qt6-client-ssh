import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Pane {
    id: root
    property var bridge

    ColumnLayout {
        anchors.fill: parent
        spacing: 8

        RowLayout {
            Layout.fillWidth: true

            Label {
                text: "Terminal"
                font.bold: true
                font.pixelSize: 16
                Layout.fillWidth: true
            }

            Button {
                text: "Effacer"
                flat: true
                onClicked: root.bridge.clearOutput()
            }
        }

        ScrollView {
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true

            TextArea {
                id: outputArea
                readOnly: true
                wrapMode: TextArea.Wrap
                font.family: "Monospace"
                font.pixelSize: 13
                color: "#d4d4d4"
                text: root.bridge.outputText

                background: Rectangle { color: "#101418" }

                onTextChanged: cursorPosition = length
            }
        }

        RowLayout {
            Layout.fillWidth: true
            spacing: 8

            TextField {
                id: commandField
                Layout.fillWidth: true
                placeholderText: "Saisir une commande puis Entrée…"
                enabled: root.bridge.connected
                onAccepted: {
                    root.bridge.sendCommand(text)
                    text = ""
                }
            }

            Button {
                text: "Envoyer"
                enabled: root.bridge.connected
                onClicked: {
                    root.bridge.sendCommand(commandField.text)
                    commandField.text = ""
                }
            }
        }
    }
}
