import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import Qt.labs.platform 1.1

ApplicationWindow {
    id: root
    // 去掉固定大小，设置最小尺寸（确保布局不崩溃）
    minimumWidth: 800
    minimumHeight: 600
    // 允许窗口最大化到屏幕尺寸（可选）
    maximumWidth: Screen.desktopAvailableWidth
    maximumHeight: Screen.desktopAvailableHeight
    title: "Scrapy Egg Generator"
    visible: true
    flags: Qt.FramelessWindowHint | Qt.Window

    /* 顶部拖动条 MouseArea：只覆盖顶部 30 像素，避免阻塞输入控件 */
    MouseArea {
        id: titleBarMouseArea
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.top: parent.top
        height: 30
        propagateComposedEvents: true // 关键：事件透传到下层控件
        hoverEnabled: true

        onPressed: {
            // 仅在此 MouseArea 中允许移动窗口
            root.startSystemMove();
        }

        // 不拦截点击事件，允许下层控件响应
        onClicked: mouse.accepted = false;
    }
    // ------------------------------
    // 全局状态
    // ------------------------------
    property bool isGenerating: false  // 防止重复点击
    property var currentProjectPath: ""

    // ------------------------------
    // 连接Python后端
    // ------------------------------
    // 从main.py注入的Generator实例（通过 context property 注入；不要在 QML 内再次声明）

    // ------------------------------
    // 组件定义
    // ------------------------------
    // 错误提示对话框
    Component {
        id: errorDialog
        Popup {
            id: errorDlg
            property string message: ""
            modal: true
            focus: true
            width: Math.min(parent.width * 0.8, 600)
            anchors.centerIn: root.contentItem

            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 16
                spacing: 12

                Text {
                    text: errorDlg.message
                    wrapMode: Text.Wrap
                    Layout.fillWidth: true
                }

                RowLayout {
                    Layout.alignment: Qt.AlignRight
                    Button {
                        text: "确定"
                        onClicked: errorDlg.close()
                    }
                }
            }
        }
    }

    // 项目覆盖确认对话框
    Component {
        id: overwriteDialog
        Popup {
            id: overwriteDlg
            property string projectPath: ""
            modal: true
            focus: true
            width: Math.min(parent.width * 0.8, 600)
            anchors.centerIn: root.contentItem

            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 16
                spacing: 12

                Text {
                    text: `项目 "${overwriteDlg.projectPath}" 已存在，是否覆盖？`
                    wrapMode: Text.Wrap
                    Layout.fillWidth: true
                }

                RowLayout {
                    spacing: 8
                    Layout.alignment: Qt.AlignRight
                    Button {
                        text: "是"
                        onClicked: {
                            if (generator) generator.confirmOverwrite(true)
                            overwriteDlg.close()
                        }
                    }
                    Button {
                        text: "否"
                        onClicked: {
                            if (generator) generator.confirmOverwrite(false)
                            overwriteDlg.close()
                        }
                    }
                }
            }
        }
    }

    // ------------------------------
    // 主界面布局
    // ------------------------------
    ColumnLayout {
        id: mainLayout
        anchors.top: titleBarMouseArea.bottom
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        anchors.margins: 10
        visible: !isGenerating

        // 1. 标签栏（TabBar）
        TabBar {
            id: tabBar
            Layout.fillWidth: true

            // 标签按钮（对应4个页面）
            TabButton { text: "项目信息" }
            TabButton { text: "爬虫配置" }
            TabButton { text: "Scrapy配置" }
            TabButton { text: "生成结果" }
            onCurrentIndexChanged: swipeView.currentIndex = currentIndex
        }

        // 2. 内容区域（SwipeView：滑动切换页面）
        StackLayout {
            id: swipeView
            Layout.fillWidth: true
            Layout.fillHeight: true
            currentIndex: tabBar.currentIndex // 与TabBar同步

            // ------------------------------
            // 页面1：项目信息（原第一个Tab内容）
            // ------------------------------
            ColumnLayout {
                Layout.fillWidth: true
                Layout.fillHeight: true
                Layout.margins: 10
                spacing: 12

                TextField {
                    Layout.fillWidth: true
                    placeholderText: "项目名称（如my_spider_project）"
                    text: generator ? generator.projectName : ""
                    onTextChanged: if (generator) generator.projectName = text
                    enabled: !isGenerating
                }

                TextField {
                    Layout.fillWidth: true
                    placeholderText: "爬虫名称（如example_spider）"
                    text: generator ? generator.spiderName : ""
                    onTextChanged: if (generator) generator.spiderName = text
                    enabled: !isGenerating
                }
            }

            // ------------------------------
            // 页面2：爬虫配置（原第二个Tab内容）
            // ------------------------------
            ColumnLayout {
                Layout.fillWidth: true
                Layout.fillHeight: true
                Layout.margins: 10
                spacing: 12

                TextArea {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 120
                    placeholderText: "起始URL（每行一个，如https://example.com）"
                    text: generator ? generator.startUrls : ""
                    onTextChanged: if (generator) generator.startUrls = text
                    enabled: !isGenerating
                    wrapMode: TextArea.Wrap
                }

                TextArea {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 120
                    placeholderText: "允许的域名（每行一个，如example.com）"
                    text: generator ? generator.allowedDomains : ""
                    onTextChanged: if (generator) generator.allowedDomains = text
                    enabled: !isGenerating
                    wrapMode: TextArea.Wrap
                }

                TextArea {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 150
                    placeholderText: "Parse方法代码（如提取标题）"
                    text: generator ? generator.parseCode : ""
                    onTextChanged: if (generator) generator.parseCode = text
                    enabled: !isGenerating
                    wrapMode: TextArea.Wrap
                }
            }

            // ------------------------------
            // 页面3：Scrapy配置（原第三个Tab内容）
            // ------------------------------
            ColumnLayout {
                Layout.fillWidth: true
                Layout.fillHeight: true
                Layout.margins: 10
                spacing: 12

                TextField {
                    Layout.fillWidth: true
                    placeholderText: "User-Agent（如Mozilla/5.0 (...)）"
                    text: generator ? generator.userAgent : ""
                    onTextChanged: if (generator) generator.userAgent = text
                    enabled: !isGenerating
                }

                CheckBox {
                    text: "遵守Robots.txt协议"
                    checked: generator ? generator.robotstxtObey : true
                    onCheckedChanged: if (generator) generator.robotstxtObey = checked
                    enabled: !isGenerating
                }

                RowLayout {
                    spacing: 8
                    Label { text: "并发请求数：" }
                    TextField {
                            id: concurrentField
                            Layout.preferredWidth: 80
                            placeholderText: "16"
                            text: generator ? (generator.concurrentRequests === undefined || generator.concurrentRequests === null ? "" : generator.concurrentRequests.toString()) : ""
                            onTextChanged: {
                                const value = parseInt(text)
                                if (!isNaN(value) && generator) generator.concurrentRequests = value
                            }
                            enabled: !isGenerating
                            inputMethodHints: Qt.ImhDigitsOnly
                        }
                }

                RowLayout {
                    spacing: 8
                    Label { text: "下载延迟（秒）：" }
                        TextField {
                        id: delayField
                        Layout.preferredWidth: 80
                        placeholderText: "0.0"
                        text: generator ? (generator.downloadDelay === undefined || generator.downloadDelay === null ? "" : generator.downloadDelay.toString()) : ""
                        onTextChanged: {
                            const value = parseFloat(text)
                            if (!isNaN(value) && generator) generator.downloadDelay = value
                        }
                        enabled: !isGenerating
                        inputMethodHints: Qt.ImhDigitsOnly | Qt.ImhPreferNumbers
                    }
                }
            }

            // ------------------------------
            // 页面4：生成结果（原第四个Tab内容）
            // ------------------------------
            ColumnLayout {
                Layout.fillWidth: true
                Layout.fillHeight: true
                Layout.margins: 10
                spacing: 12

                TextArea {
                    id: logArea
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    readOnly: true
                    text: generator ? generator.logText : ""
                    wrapMode: TextArea.Wrap
                    // 自动滚动到底部（仅当 verticalScrollBar 可用时）
                    onTextChanged: {
                        if (logArea.verticalScrollBar) logArea.verticalScrollBar.position = 1.0
                    }
                }

                Button {
                    text: "打开Egg目录"
                    enabled: (generator ? generator.eggPath !== "" : false) && !isGenerating
                    onClicked: if (generator) generator.openEggDir()
                }
            }
        }
    }

    // ------------------------------
    // 底部操作按钮
    // ------------------------------
    Button {
        id: generateBtn
        text: isGenerating ? "生成中..." : "生成Egg文件"
        anchors.bottom: parent.bottom
        anchors.right: parent.right
        anchors.margins: 16
        enabled: !isGenerating
        onClicked: {
            isGenerating = true
            if (generator) generator.generateEgg()
            else {
                isGenerating = false
                console.warn("generator not available to start generation")
            }
        }
    }

    // ------------------------------
    // 信号连接
    // ------------------------------
    Component.onCompleted: {
        if (generator) {
            // 日志更新：自动滚动到底部
            generator.logUpdated.connect((text) => {
                logArea.text = text
                if (logArea.verticalScrollBar) logArea.verticalScrollBar.position = 1.0
            })

            // 错误提示
            generator.errorOccurred.connect((message) => {
                const dialog = errorDialog.createObject(root)
                dialog.message = message
                dialog.open()
                isGenerating = false
            })

            // 项目存在：弹确认框
            generator.projectExists.connect((path) => {
                const dialog = overwriteDialog.createObject(root)
                dialog.projectPath = path
                dialog.open()
            })

            // 生成完成
            generator.eggGenerated.connect(() => {
                isGenerating = false
            })
        } else {
            console.warn("generator context property not available on Component.onCompleted")
        }
    }
}