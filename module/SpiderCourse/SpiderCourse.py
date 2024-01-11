# 爬虫北化在线模块
import requests
from lxml import etree
from random import randint
import re

from module.SpiderJWS.SpiderJwxt import SpiderJwxt

# 随机请求的User-Agent
USER_AGENTS = [
    "Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1; AcooBrowser; .NET CLR 1.1.4322; .NET CLR 2.0.50727)",
    "Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 6.0; Acoo Browser; SLCC1; .NET CLR 2.0.50727; Media Center PC 5.0; .NET CLR 3.0.04506)",
    "Mozilla/4.0 (compatible; MSIE 7.0; AOL 9.5; AOLBuild 4337.35; Windows NT 5.1; .NET CLR 1.1.4322; .NET CLR 2.0.50727)",
    "Mozilla/5.0 (Windows; U; MSIE 9.0; Windows NT 9.0; en-US)",
    "Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; Win64; x64; Trident/5.0; .NET CLR 3.5.30729; .NET CLR 3.0.30729; .NET CLR 2.0.50727; Media Center PC 6.0)",
    "Mozilla/5.0 (compatible; MSIE 8.0; Windows NT 6.0; Trident/4.0; WOW64; Trident/4.0; SLCC2; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729; .NET CLR 1.0.3705; .NET CLR 1.1.4322)",
    "Mozilla/4.0 (compatible; MSIE 7.0b; Windows NT 5.2; .NET CLR 1.1.4322; .NET CLR 2.0.50727; InfoPath.2; .NET CLR 3.0.04506.30)",
    "Mozilla/5.0 (Windows; U; Windows NT 5.1; zh-CN) AppleWebKit/523.15 (KHTML, like Gecko, Safari/419.3) Arora/0.3 (Change: 287 c9dfb30)",
    "Mozilla/5.0 (X11; U; Linux; en-US) AppleWebKit/527+ (KHTML, like Gecko, Safari/419.3) Arora/0.6",
    "Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.8.1.2pre) Gecko/20070215 K-Ninja/2.1.1",
    "Mozilla/5.0 (Windows; U; Windows NT 5.1; zh-CN; rv:1.9) Gecko/20080705 Firefox/3.0 Kapiko/3.0",
    "Mozilla/5.0 (X11; Linux i686; U;) Gecko/20070322 Kazehakase/0.4.5",
    "Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.8) Gecko Fedora/1.9.0.8-1.fc10 Kazehakase/0.5.6",
    "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/535.11 (KHTML, like Gecko) Chrome/17.0.963.56 Safari/535.11",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_7_3) AppleWebKit/535.20 (KHTML, like Gecko) Chrome/19.0.1036.7 Safari/535.20",
    "Opera/9.80 (Macintosh; Intel Mac OS X 10.6.8; U; fr) Presto/2.9.168 Version/11.52",
]


class SpiderCourse:
    __url = "https://course.buct.edu.cn/meol/"  # 基础地址
    __req = requests.session()  # request请求

    def __init__(self, username, password) -> None:
        self.__user = username  # 用户名
        self.__password = password  # 密码
        self.isLogin = False  # 判断是否登录参数
        random_agent = USER_AGENTS[randint(0, len(USER_AGENTS) - 1)]
        self.__header = {
            'User-Agent': random_agent,
        }  # 请求头

    # 登录
    def login(self):
        # 请求参数
        data = {
            "IPT_LOGINUSERNAME": self.__user,
            "IPT_LOGINPASSWORD": self.__password
        }
        # 发起登录请求
        index = self.__req.post(url=self.__url + "loginCheck.do", headers=self.__header, params=data)

        # 验证是否登录
        indexUrl = str(index.url)

        if indexUrl.startswith(self.__url + "personal.do"):
            self.isLogin = True

    # 登出
    def logout(self):
        if not self.isLogin:
            return
        self.__req.get(
            url=self.__url + "homepage/V8/include/logout.jsp", headers=self.__header)
        self.isLogin = False

    # 获取用户学科列表
    def initUser(self) -> object:
        if (not self.isLogin):
            return
        # 获取网络页面
        course = self.__req.get(
            url=self.__url + "lesson/blen.student.lesson.list.jsp", headers=self.__header)
        courseXpath = SpiderCourse.__getEtree(course.text)

        # 解析内容
        courseId = courseXpath.xpath(
            '/html/body/div/table//tr/td/a[1]/@onclick')  # 获取课程Id
        courseName = courseXpath.xpath(
            '/html/body/div/table//tr/td/a[1]/text()')  # 获取课程Name
        courseTeacher = courseXpath.xpath(
            '/html/body/div/table//tr/td[3]/text()')  # 获取教师名

        # 修剪下字符串
        SpiderCourse.__trimData(courseName)
        SpiderCourse.__trimId(courseId)
        SpiderCourse.__trimData(courseTeacher)

        # 通过教务系统检查是否为本学期课程
        T = self.__checkCourse(courseName, courseId, courseTeacher)
        courseName = T[0]
        courseId = T[1]

        # 封装成字典同时检查课程是否有效
        courseList = SpiderCourse.__getCourse(courseName, courseId)

        # 添加到数据库
        # DataUtil.addtUser(self.__user, self.__password, courseList)

    # 获取作业任务
    def getTask(self, courseList):
        if not self.isLogin:
            return

        courseData = []

        # 获取作业数据
        i = 0
        while i < len(courseList):

            Id = courseList[i][1]

            courseItem = {
                "name": courseList[i][0],
                "data": []
            }

            detailUrl = self.__url + \
                        f'jpk/course/layout/newpage/index.jsp?courseId={Id}'
            # 发起请求以给网页cookie
            self.__req.get(url=detailUrl, headers=self.__header)

            # 课程作业页面
            workUrl = self.__url + 'common/hw/student/hwtask.jsp?tagbug=client&strStyle=new03'
            # 获取课程页面
            workPage = self.__req.get(url=workUrl, headers=self.__header)

            # xpath解析预处理
            workXpath = self.__getEtree(workPage.text)

            # 检查是否过于频繁，以导致暂停
            MessAlter = workXpath.xpath('/html/head/script/text()')
            Mess_flag = MessAlter[0].find("你的访问过于频繁,请稍后再试")
            if Mess_flag != -1:
                # 暂停则再跑一次
                continue

            workListXpath = workXpath.xpath('/html/body/div/table//tr')

            # 获取 ‘在线作业’ 的 ‘名称’ 和 ‘截止时间’
            for j in range(1, len(workListXpath)):
                workName = workListXpath[j].xpath('./td[1]/a/text()')
                workDeadline = workListXpath[j].xpath('./td[2]/text()')
                workStatus = workListXpath[j].xpath('./td[6]//a')

                # 当workStatus可以获取到‘提交作业’字样说明用户未提交作业，才需要爬取
                if len(workStatus) and len(workName) and len(workDeadline):
                    courseItem['data'].append({"name": workName[0], "time": workDeadline[0].strip('\n        ')})

            # 在线测试页面
            testUrl = self.__url + \
                      f"common/question/test/student/list.jsp?tagbug=client&cateId={Id}&status=1&strStyle=new03"
            # 获取测试页面
            testPage = self.__req.get(url=testUrl)
            # xpath解析预处理
            testXpath = self.__getEtree(testPage.text)
            testListXpath = testXpath.xpath('/html/body/div/table//tr')

            # 特别判断一种特殊的在线测试
            specialTest = testXpath.xpath(
                '/html/body/div/table//tr[2]/th/text()')
            if len(specialTest):
                testName = testListXpath[0].xpath('./td[1]/text()')
                testDeadline = testListXpath[2].xpath('./td[1]/text()')
                testStatus = testListXpath[5].xpath('./td[1]//a')
                if len(testStatus) and len(testName) > 0 and len(testDeadline) > 0:
                    courseItem['data'].append(
                        {"name": testName[0].strip('\n                    '), "time": testDeadline[0]})
            else:
                # 获取 ‘在线测试’ 的 ‘名称’ 和 ‘截止时间’
                for j in range(1, len(testListXpath)):
                    testName = testListXpath[j].xpath('./td[1]/text()')
                    testDeadline = testListXpath[j].xpath('./td[3]/text()')
                    testStatus = testListXpath[j].xpath('./td[6]//a')

                    if len(testStatus) and len(testName) > 0 and len(testDeadline) > 0:
                        courseItem['data'].append(
                            {"name": testName[0].strip('\n                    '), "time": testDeadline[0]})

            # 添加这个课程的内容
            if courseItem['data']:
                courseData.append(courseItem)

            i += 1

        return courseData

    # 获得str的etree
    @staticmethod
    def __getEtree(html):
        if not isinstance(html, str):
            raise RuntimeError("TypeMatchError")
        return etree.HTML(html)

    # 修建字符串左右的空格和回车
    @staticmethod
    def __trimData(data):
        if not isinstance(data, list):
            raise RuntimeError("TypeMatchError")
        for i in range(len(data)):
            data[i] = data[i].strip(" \n")

    # 修剪字符串得到用户Id
    @staticmethod
    def __trimId(data):
        if not isinstance(data, list):
            raise RuntimeError("TypeMatchError")
        for i in range(len(data)):
            data[i] = data[i][58:63]

    # 检查在线课程是否有效（即是否能够访问作业信息）
    @staticmethod
    def __getCourse(courseName, courseId):
        courseList = {}
        delitem = []
        for i in range(len(courseName)):
            detail_url = SpiderCourse.__url + \
                         f'jpk/course/layout/newpage/index.jsp?courseId={courseId[i]}'
            detail_text = SpiderCourse.__req.get(url=detail_url).text
            detailXpath = SpiderCourse.__getEtree(detail_text)
            msg = detailXpath.xpath('/html/head/title/text()')
            if msg[0] == '错误！':
                delitem.append(i)

        for i in range(len(courseId)):
            if i in delitem:
                continue

            count = 1
            name = courseName[i]
            while name in courseList.keys():
                count += 1
                name = courseName[i] + "-" + str(count)
            courseList[name] = courseId[i]

        return courseList

    def __checkCourse(self, courseName, courseId, courseTeacher):
        rb = SpiderJwxt(self.__user, self.__password)
        rb.login()
        if not rb.isLogin():
            return courseName, courseId

        courseList = rb.getCourse()
        tName = []
        tId = []
        for i in range(len(courseName)):
            flag = 0
            for j in range(len(courseList)):
                pos1 = courseList[j]["courseName"].find(courseName[i])
                pos2 = courseList[j]["courseTeacher"].find(courseTeacher[i])

                if (not pos1 == -1) or (not pos2 == -1):
                    flag = 1
                    break
            if flag:
                tName.append(courseName[i])
                tId.append(courseId[i])

        return tName, tId

    # 获取课程提醒
    def getReminder(self):
        if not self.isLogin:
            return

        personalPage = self.__req.get(
            url="https://course.buct.edu.cn/meol/welcomepage/student/interaction_reminder_v8.jsp?r=1",
            headers=self.__header
        )

        courseId = re.findall(r"lid=(\d{5})", personalPage.text)  # 获取课程id
        courseName = etree.HTML(personalPage.text).xpath('//div/ul/li/ul/li/a/text()')  # 获取课程名字
        SpiderCourse.__trimData(courseName)

        courseList = set(zip(courseName, courseId))  # 封装，且过滤相同元素

        return list(courseList)

    # 获取课程提醒作业
    def getTask_by_reminder(self):
        self.login()  # 登录

        if not self.isLogin:
            return {
                "data": [],
                "msg": "登录失败，请检查北化在线密码是否正确",
                "status": False
            }

        reminder = self.getReminder()
        data = self.getTask(reminder)  # 获取作业信息

        self.logout()  # 登出
        return {
            "data": data,
            "msg": "获取作业信息成功",
            "status": True
        }


if __name__ == "__main__":
    pass
