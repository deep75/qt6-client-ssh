import QtQuick
import QtQuick.Controls
import QtQuick.Controls.Material
import QtQuick.Layouts
import QtQuick.Dialogs

Pane {
    id: root
    property var bridge
    property string authMethod: "password"

    Material.elevation: 2

    ColumnLayout {
        anchors.fill: parent
        spacing: 14

        Label {
            text: "Nouvelle connexion"
            font.bold: true
            font.pixelSize: 16
        }

        GroupBox {
            title: "Serveur"
            Layout.fillWidth: true

            ColumnLayout {
                anchors.fill: parent
                spacing: 8

                Label { text: "Hôte" }
                TextField {
                    id: hostField
                    Layout.fillWidth: true
                    placeholderText: "ex: serveur.example.com"
                }

                Label { text: "Port" }
                SpinBox {
                    id: portField
                    from: 1
                    to: 65535
                    value: 22
                    editable: true
                    Layout.fillWidth: true
                }

                Label { text: "Utilisateur" }
                TextField {
                    id: usernameField
                    Layout.fillWidth: true
                    placeholderText: "ex: admin"
                }

                Label { text: "Délai de connexion (s)" }
                SpinBox {
                    id: timeoutField
                    from: 1
                    to: 120
                    value: 10
                    editable: true
                    Layout.fillWidth: true
                }
            }
        }

        GroupBox {
            title: "Authentification"
            Layout.fillWidth: true

            ColumnLayout {
                anchors.fill: parent
                spacing: 8

                RowLayout {
                    RadioButton {
                        id: passwordRadio
                        text: "Mot de passe"
                        checked: true
                        onCheckedChanged: if (checked) root.authMethod = "password"
                    }
                    RadioButton {
                        id: keyRadio
                        text: "Clé privée"
                        onCheckedChanged: if (checked) root.authMethod = "key"
                    }
                }

                TextField {
                    id: passwordField
                    Layout.fillWidth: true
                    echoMode: TextInput.Password
                    placeholderText: "Mot de passe"
                    enabled: root.authMethod === "password"
                }

                RowLayout {
                    Layout.fillWidth: true
                    visible: root.authMethod === "key"

                    TextField {
                        id: keyPathField
                        Layout.fillWidth: true
                        placeholderText: "~/.ssh/id_ed25519"
                    }
                    Button {
                        text: "Parcourir…"
                        onClicked: keyFileDialog.open()
                    }
                }

                TextField {
                    id: passphraseField
                    Layout.fillWidth: true
                    echoMode: TextInput.Password
                    placeholderText: "Phrase secrète (optionnelle)"
                    enabled: root.authMethod === "key"
                }
            }
        }

        RowLayout {
            Layout.fillWidth: true
            spacing: 8

            Button {
                text: "Se connecter"
                Layout.fillWidth: true
                highlighted: true
                enabled: !root.bridge.connected
                    && hostField.text.length > 0
                    && usernameField.text.length > 0
                onClicked: root.bridge.connectToHost(
                    hostField.text,
                    portField.value,
                    usernameField.text,
                    root.authMethod,
                    passwordField.text,
                    keyPathField.text,
                    passphraseField.text,
                    timeoutField.value
                )
            }

            Button {
                text: "Déconnecter"
                Layout.fillWidth: true
                enabled: root.bridge.connected
                onClicked: root.bridge.disconnectFromHost()
            }
        }

        Item { Layout.fillHeight: true }
    }

    FileDialog {
        id: keyFileDialog
        title: "Sélectionner une clé privée"
        onAccepted: keyPathField.text = root.bridge.toLocalPath(selectedFile)
    }
}
