import QtQuick
import QtQuick.Controls
import QtQuick.Controls.Material
import QtQuick.Layouts
import SshClient 1.0

ApplicationWindow {
    id: window
    width: 1080
    height: 680
    visible: true
    title: "Client SSH — PySide6 / QML"

    Material.theme: Material.Dark
    Material.accent: Material.LightBlue

    SshBridge {
        id: bridge
    }

    Connections {
        target: bridge
        function onErrorOccurred(message) {
            errorBanner.text = message
            errorBanner.visible = true
            errorTimer.restart()
        }
    }

    Timer {
        id: errorTimer
        interval: 6000
        onTriggered: errorBanner.visible = false
    }

    header: ToolBar {
        RowLayout {
            anchors.fill: parent
            anchors.margins: 8

            Label {
                text: "Client SSH"
                font.bold: true
                font.pixelSize: 18
            }

            Item { Layout.fillWidth: true }

            Rectangle {
                width: 10
                height: 10
                radius: 5
                color: bridge.connected ? "#4caf50" : "#9e9e9e"
                Layout.alignment: Qt.AlignVCenter
            }

            Label {
                text: bridge.status
                Layout.alignment: Qt.AlignVCenter
            }
        }
    }

    RowLayout {
        anchors.fill: parent
        anchors.margins: 12
        spacing: 12

        ConnectionForm {
            bridge: bridge
            Layout.preferredWidth: 340
            Layout.fillHeight: true
        }

        OutputPanel {
            bridge: bridge
            Layout.fillWidth: true
            Layout.fillHeight: true
        }
    }

    Rectangle {
        id: errorBanner
        property alias text: errorLabel.text
        visible: false
        color: "#c62828"
        radius: 6
        anchors.bottom: parent.bottom
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.bottomMargin: 16
        width: Math.min(parent.width - 40, errorLabel.implicitWidth + 40)
        height: errorLabel.implicitHeight + 20

        Label {
            id: errorLabel
            anchors.centerIn: parent
            color: "white"
            wrapMode: Text.WordWrap
        }
    }
}
