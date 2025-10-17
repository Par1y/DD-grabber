from PySide6.QtCore import QObject, Property, Signal, Slot, QUrl
from PySide6.QtGui import QDesktopServices
import subprocess
import os
import re
import glob
import shutil


class Generator(QObject):
    # Signals
    logUpdated = Signal(str)
    errorOccurred = Signal(str)
    projectExists = Signal(str)
    eggGenerated = Signal()

    projectNameChanged = Signal()
    spiderNameChanged = Signal()
    startUrlsChanged = Signal()
    allowedDomainsChanged = Signal()
    parseCodeChanged = Signal()
    userAgentChanged = Signal()
    robotstxtObeyChanged = Signal()
    concurrentRequestsChanged = Signal()
    downloadDelayChanged = Signal()
    outputDirChanged = Signal()

    def __init__(self):
        super().__init__()
        self._projectName = ""
        self._spiderName = ""
        self._startUrls = ""
        self._allowedDomains = ""
        self._parseCode = "# 示例：提取标题\n# title = response.css('title::text').get()\n# yield {'title': title}"
        self._userAgent = ""
        self._robotstxtObey = True
        self._concurrentRequests = 16
        self._downloadDelay = 0.0
        self._outputDir = os.getcwd()
        self._logText = ""
        self._eggPath = ""
        self._currentParams = None

    # Properties
    @Property(str, notify=logUpdated)
    def logText(self):
        return self._logText

    @Property(str, notify=eggGenerated)
    def eggPath(self):
        return self._eggPath

    @Property(str, notify=projectNameChanged)
    def projectName(self):
        return self._projectName

    @projectName.setter
    def projectName(self, value):
        if self._projectName != value:
            self._projectName = value
            self.projectNameChanged.emit()

    @Property(str, notify=spiderNameChanged)
    def spiderName(self):
        return self._spiderName

    @spiderName.setter
    def spiderName(self, value):
        if self._spiderName != value:
            self._spiderName = value
            self.spiderNameChanged.emit()

    @Property(str, notify=startUrlsChanged)
    def startUrls(self):
        return self._startUrls

    @startUrls.setter
    def startUrls(self, value):
        if self._startUrls != value:
            self._startUrls = value
            self.startUrlsChanged.emit()

    @Property(str, notify=allowedDomainsChanged)
    def allowedDomains(self):
        return self._allowedDomains

    @allowedDomains.setter
    def allowedDomains(self, value):
        if self._allowedDomains != value:
            self._allowedDomains = value
            self.allowedDomainsChanged.emit()

    @Property(str, notify=parseCodeChanged)
    def parseCode(self):
        return self._parseCode

    @parseCode.setter
    def parseCode(self, value):
        if self._parseCode != value:
            self._parseCode = value
            self.parseCodeChanged.emit()

    @Property(str, notify=userAgentChanged)
    def userAgent(self):
        return self._userAgent

    @userAgent.setter
    def userAgent(self, value):
        if self._userAgent != value:
            self._userAgent = value
            self.userAgentChanged.emit()

    @Property(bool, notify=robotstxtObeyChanged)
    def robotstxtObey(self):
        return self._robotstxtObey

    @robotstxtObey.setter
    def robotstxtObey(self, value):
        if self._robotstxtObey != value:
            self._robotstxtObey = value
            self.robotstxtObeyChanged.emit()

    @Property(int, notify=concurrentRequestsChanged)
    def concurrentRequests(self):
        return self._concurrentRequests

    @concurrentRequests.setter
    def concurrentRequests(self, value):
        if self._concurrentRequests != value:
            self._concurrentRequests = value
            self.concurrentRequestsChanged.emit()

    @Property(float, notify=downloadDelayChanged)
    def downloadDelay(self):
        return self._downloadDelay

    @downloadDelay.setter
    def downloadDelay(self, value):
        if self._downloadDelay != value:
            self._downloadDelay = value
            self.downloadDelayChanged.emit()

    @Property(str, notify=outputDirChanged)
    def outputDir(self):
        return self._outputDir

    @outputDir.setter
    def outputDir(self, value):
        if self._outputDir != value:
            self._outputDir = value
            self.outputDirChanged.emit()
            try:
                self.appendLog(f"输出目录已更新：{self._outputDir}")
            except Exception:
                pass

    # Slots / actions
    @Slot()
    def selectOutputDir(self):
        dir_path = os.getcwd()
        self._outputDir = dir_path
        self.appendLog(f"输出目录设置为：{self._outputDir} (默认 当前工作目录)")

    @Slot()
    def openEggDir(self):
        if self._eggPath:
            QDesktopServices.openUrl(QUrl.fromLocalFile(os.path.dirname(self._eggPath)))

    @Slot()
    def generateEgg(self):
        self.clearLog()
        try:
            self._currentParams = self._collectParams()
            self._validateParams(self._currentParams)
            self.appendLog("参数验证通过")
        except ValueError as e:
            self.errorOccurred.emit(str(e))
            return

        project_path = os.path.join(self._outputDir, self._currentParams["projectName"])
        if os.path.exists(project_path):
            self.projectExists.emit(project_path)
        else:
            self._continueGenerate(project_path)

    @Slot(bool)
    def confirmOverwrite(self, confirm):
        if not confirm:
            self.appendLog("生成取消：用户拒绝覆盖项目")
            return

        project_path = os.path.join(self._outputDir, self._currentParams["projectName"])
        shutil.rmtree(project_path)
        self.appendLog(f"已删除现有项目：{project_path}")
        self._continueGenerate(project_path)

    def _continueGenerate(self, project_path):
        try:
            self.appendLog(f"正在生成Scrapy项目：{self._currentParams['projectName']}")
            if shutil.which("scrapy") is None:
                raise FileNotFoundError("scrapy 命令未找到，请先安装 scrapy (pip install scrapy) 或确保 scrapy 在 PATH 中")

            subprocess.run(
                ["scrapy", "startproject", self._currentParams["projectName"]],
                cwd=self._outputDir,
                check=True,
                capture_output=True,
                text=True
            )
            self.appendLog(f"项目生成成功：{project_path}")
        except subprocess.CalledProcessError as e:
            self.errorOccurred.emit(f"项目生成失败：{e.stderr}")
            return
        except FileNotFoundError as e:
            self.errorOccurred.emit(str(e))
            return

        try:
            self._generateSpiderFile(project_path)
            self.appendLog("爬虫文件生成成功")
        except Exception as e:
            self.errorOccurred.emit(f"爬虫文件生成失败：{str(e)}")
            return

        try:
            self._modifySettingsFile(project_path)
            self.appendLog("settings.py修改成功")
        except Exception as e:
            self.errorOccurred.emit(f"settings.py修改失败：{str(e)}")
            return

        try:
            self.appendLog("正在打包Egg文件...")
            try:
                setup_py = os.path.join(project_path, "setup.py")
                if not os.path.exists(setup_py):
                    pkg_name = self._currentParams['projectName']
                    minimal_setup = f'''from setuptools import setup, find_packages

setup(
    name="{pkg_name}",
    version="0.1.0",
    packages=find_packages(),
    include_package_data=True,
    description='Scrapy project {pkg_name} generated by DD-grabber',
    entry_points={{
        'scrapy': [
            'settings = {pkg_name}.settings'
        ]
    }},
)
'''
                    with open(setup_py, 'w', encoding='utf-8') as f:
                        f.write(minimal_setup)
                    self.appendLog("已生成最小 setup.py 用于打包")
            except Exception as e:
                self.appendLog(f"生成 setup.py 失败：{str(e)}")

            subprocess.run(
                ["python", "setup.py", "bdist_egg"],
                cwd=project_path,
                check=True,
                capture_output=True,
                text=True
            )
            egg_files = glob.glob(os.path.join(project_path, "dist", "*.egg"))
            if not egg_files:
                raise FileNotFoundError("未找到生成的Egg文件")
            self._eggPath = egg_files[0]
            self.appendLog(f"Egg生成成功：{self._eggPath}")
            self.eggGenerated.emit()
        except subprocess.CalledProcessError as e:
            self.errorOccurred.emit(f"打包失败：{e.stderr}")
            return
        except Exception as e:
            self.errorOccurred.emit(f"打包失败：{str(e)}")
            return

    # Helpers
    def appendLog(self, text):
        self._logText += text + "\n"
        self.logUpdated.emit(self._logText)

    def clearLog(self):
        self._logText = ""
        self.logUpdated.emit(self._logText)

    def _collectParams(self):
        return {
            "projectName": self._projectName.strip(),
            "spiderName": self._spiderName.strip(),
            "startUrls": [line.strip() for line in self._startUrls.splitlines() if line.strip()],
            "allowedDomains": [line.strip() for line in self._allowedDomains.splitlines() if line.strip()],
            "parseCode": self._parseCode.strip(),
            "userAgent": self._userAgent.strip(),
            "robotstxtObey": self._robotstxtObey,
            "concurrentRequests": self._concurrentRequests,
            "downloadDelay": self._downloadDelay
        }

    def _validateParams(self, params):
        if not params["projectName"]:
            raise ValueError("项目名称不能为空")
        if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", params["projectName"]):
            raise ValueError("项目名称只能包含字母、数字和下划线，且不能以数字开头")
        if not params["spiderName"]:
            raise ValueError("爬虫名称不能为空")
        if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", params["spiderName"]):
            raise ValueError("爬虫名称只能包含字母、数字和下划线，且不能以数字开头")
        if not params["startUrls"]:
            raise ValueError("起始URL不能为空")
        for url in params["startUrls"]:
            if not re.match(r"^https?://", url):
                raise ValueError(f"URL格式错误：{url}（需以http/https开头）")

    def _generateSpiderFile(self, project_path):
        spider_dir = os.path.join(project_path, self._currentParams["projectName"], "spiders")
        spider_file = os.path.join(spider_dir, f"{self._currentParams['spiderName']}.py")
        spider_template = f"""import scrapy

class {self._currentParams['spiderName'].capitalize()}Spider(scrapy.Spider):
    name = "{self._currentParams['spiderName']}"
    start_urls = {self._currentParams['startUrls']}
    allowed_domains = {self._currentParams['allowedDomains']}

    def parse(self, response):
        {self._indentParseCode(self._currentParams['parseCode'])}
"""
        with open(spider_file, "w", encoding="utf-8") as f:
            f.write(spider_template.strip())

    def _indentParseCode(self, code):
        lines = [line.strip() for line in code.splitlines() if line.strip()]
        return "\n        ".join(lines) if lines else "# 请在此编写解析逻辑"

    def _modifySettingsFile(self, project_path):
        settings_path = os.path.join(project_path, self._currentParams["projectName"], "settings.py")
        with open(settings_path, "r", encoding="utf-8") as f:
            content = f.read()

        if self._currentParams["userAgent"]:
            content = re.sub(r"^#?USER_AGENT = .*$", f'USER_AGENT = "{self._currentParams["userAgent"]}"', content, flags=re.M)
        else:
            content = re.sub(r"^#?USER_AGENT = .*$", '# USER_AGENT = "scrapy/2.11.0 (+https://scrapy.org)"', content, flags=re.M)

        # Ensure Python boolean literals (True/False), not 'true'/'false'
        robot_val = 'True' if self._currentParams["robotstxtObey"] else 'False'
        content = re.sub(r"^#?ROBOTSTXT_OBEY = .*$", f'ROBOTSTXT_OBEY = {robot_val}', content, flags=re.M)
        content = re.sub(r"^#?CONCURRENT_REQUESTS = .*$", f'CONCURRENT_REQUESTS = {self._currentParams["concurrentRequests"]}', content, flags=re.M)
        content = re.sub(r"^#?DOWNLOAD_DELAY = .*$", f'DOWNLOAD_DELAY = {self._currentParams["downloadDelay"]}', content, flags=re.M)

        with open(settings_path, "w", encoding="utf-8") as f:
            f.write(content)
