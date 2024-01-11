import re
import time
import requests
import datetime
import json
from bs4 import BeautifulSoup
from module.SpiderJWS import RSAJS
from module.SpiderJWS.hex2b64 import HB64


class SpiderJwxt(object):
    def __init__(self, username, password):
        self.baseUrl = "https://jwglxt-proxy3.buct.edu.cn"
        self.__username = username
        self.__password = password
        self.__req = requests.session()
        self.__modulus = None
        self.__exponent = None
        self.isLogin = False  # 登录状态
        self.__indexCode = ''  # 主页HTML代码
        self.nowTime = int(time.time())
        self.useVpn = False  # 是否使用vpn
        self.__xnm = SpiderJwxt.getTerm()[0]
        self.__xqm = SpiderJwxt.getTerm()[1]
        self.header = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.86 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
            "Accept-Encoding": "gzip, deflate",
            "Accept-Language": "zh-CN,zh;q=0.9",
            "Cache-Control": "max-age=0",
            "Connection": "keep-alive",
            "Referer": self.baseUrl + '/jwglxt/xtgl/login_slogin.html?language=zh_CN&_t=' + str(self.nowTime),
            "Upgrade-Insecure-Requests": "1",
        }
        self.csrfToken = None

    # 根据公匙加密密码
    def __RSAkey(self):
        rsaKey = RSAJS.RSAKey()
        rsaKey.setPublic(HB64().b642hex(self.__modulus), HB64().b642hex(self.__exponent))
        return HB64().hex2b64(rsaKey.encrypt(self.__password))

    # 得到RSA加密公匙
    def _getPublicKey(self):
        _path = '/jwglxt'
        modulusPath = self.baseUrl + _path + '/xtgl/login_getPublicKey.html?time=' + str(self.nowTime)
        backJson = json.loads(self.__req.get(modulusPath).text)
        self.__modulus = backJson['modulus']
        self.__exponent = backJson['exponent']

    # 得到隐藏域表单数据(CSRFToken)
    def _getCSRFToken(self):
        rep = self.__req.get(self.baseUrl + '/jwglxt/xtgl/login_slogin.html?language=zh_CN&_t=' + str(self.nowTime))
        csrfPattern = '<input type="hidden" id="csrftoken" name="csrftoken" value="(.*?)"/>'
        self.csrfToken = re.findall(csrfPattern, rep.text)
        if len(self.csrfToken) >= 1:
            self.csrfToken = self.csrfToken[0]

    # 登陆
    def login(self):
        if self.isLogin:
            return True

        # 模拟用户登录
        self._getCSRFToken()
        self._getPublicKey()
        enpassword = self.__RSAkey()

        # 需要发送的表单数据
        data = {
            'yhm': self.__username,
            'mm': enpassword,
            'csrftoken': self.csrfToken
        }
        rep = self.__req.post(self.baseUrl + '/jwglxt/xtgl/login_slogin.html', data=data, headers=self.header)
        if str(rep.url).startswith(self.baseUrl + '/jwglxt/xtgl/index_initMenu.html'):
            self.isLogin = True
            self.__indexCode = rep.text
            self.getUserInfo()
        else:
            self.isLogin = False

    # 得到登录用户的信息
    def getUserInfo(self):
        if not self.isLogin:
            return
        apiUrl = '/jwglxt/xtgl/index_cxYhxxIndex.html?xt=jw&localeKey=zh_CN&_=' + str(
            self.nowTime) + '&gnmkdm=index&su=' + self.__username
        rep = self.__req.get(self.baseUrl + apiUrl)
        BS = BeautifulSoup(rep.text, 'html.parser')
        try:
            name = BS.select_one('.media-body>h4').text  # 得到姓名
            classInfo = BS.select_one('.media-body>p').text  # 得到年级班级信息
            headImgUrl = BS.select_one('.media-object').attrs['src']  # 得到照片的URL
        except AttributeError:
            name = classInfo = headImgUrl = ''
        # if __name__ == '__main__':
        #     print(name)
        #     print(classInfo)
        return {
            'name': name,
            'classInfo': classInfo,
            'headImgInfo': headImgUrl
        }

    # 得到考试时间
    def getExamTime(self):
        if not self.isLogin:
            return None
        examTimeUrl = self.baseUrl + '/jwglxt/design/funcData_cxFuncDataList.html?func_widget_guid=58944B9C2CD784DBE053839D04CA5AD7&gnmkdm=N358163&su=' + self.__username
        datas = {
            '_search': False,
            'nd': self.nowTime,
            'queryModel.showCount': 15,
            'queryModel.currentPage': 1,
            'queryModel.sortName': ' ',
            'queryModel.sortOrder': 'asc',
        }

        head = self.header
        head['X-Requested-With'] = 'XMLHttpRequest'
        head['Referer'] = examTimeUrl
        head['Accept'] = 'application/json, text/javascript, */*; q=0.01'
        head['Content-Type'] = 'application/x-www-form-urlencoded;charset=UTF-8'
        if 'Upgrade-Insecure-Requests' in head:
            head.pop('Upgrade-Insecure-Requests')
        rep = self.__req.post(
            self.baseUrl + '/jwglxt/design/funcData_cxFuncDataList.html?func_widget_guid=58944B9C2CD784DBE053839D04CA5AD7&gnmkdm=N358163',
            data=datas, headers=head)
        examTime = json.loads(rep.text)
        # print(examTime)

        info = []
        pattern = re.compile(r'^(\d+?)\-(\d+?)\-(\d+?) (\d+?)\:(\d+?)\-(\d+?)\:(\d+?)$')
        for i in examTime['items']:
            dict = {'kcmc': i['kcmc'], 'cdmc': '暂无', 'kssj': i['kssj'], 'jsxx': '暂无'}
            # 正则表达式修改时间格式
            patternMatch = pattern.findall(dict['kssj'])
            if len(patternMatch):
                dict['kssj'] = '{0}-{1}-{2}({3}:{4}-{5}:{6})'.format(*patternMatch[0])
            info.append(dict)
        return info

    # 得到考试信息
    def getExamInfo(self):
        if not self.isLogin:
            return None
        self.__xqm = [3, 12, 16][int(self.__xqm) - 1]
        # ksmcdmb_id，需要动态获取
        ksmcList = []
        rep = self.__req.post(self.baseUrl + '/jwglxt/ksglcommon/common_cxKsmcByXnxq.html?gnmkdm=N358105', data={
            'xqm': self.__xqm,
            'xnm': self.__xnm
        }, headers=self.header)
        ksmcdmbJSON = json.loads(rep.text)
        for i in ksmcdmbJSON:
            ksmcList.append(i['KSMCDMB_ID'])
        # print(ksmcList)
        # 获取考试信息
        examInfoUrl = self.baseUrl + '/jwglxt/kwgl/kscx_cxXsksxxIndex.html?gnmkdm=N358105&layout=default&su=' + self.__username
        datas = {
            'xnm': self.__xnm,
            'xqm': self.__xqm,
            'ksmcdmb_id': '',
            '_search': False,
            'nd': self.nowTime,
            'queryModel.showCount': 30,
            'queryModel.currentPage': 1,
            'queryModel.sortName': ' ',
            'queryModel.sortOrder': 'asc',
            'time': 1
        }
        head = self.header
        head['X-Requested-With'] = 'XMLHttpRequest'
        head['Referer'] = examInfoUrl
        head['Accept'] = 'application/json, text/javascript, */*; q=0.01'
        head['Content-Type'] = 'application/x-www-form-urlencoded;charset=UTF-8'
        if 'Upgrade-Insecure-Requests' in head:
            head.pop('Upgrade-Insecure-Requests')
        ksxxList = []
        for j in range(len(ksmcList)):
            datas['ksmcdmb_id'] = ksmcList[j]
            rep = self.__req.post(self.baseUrl + '/jwglxt/kwgl/kscx_cxXsksxxIndex.html?doType=query&gnmkdm=N358105',
                                  data=datas, headers=head)
            examInfoJSON = json.loads(rep.text)
            for i in examInfoJSON['items']:
                ksxxList.append(i)
            if __name__ == "__main__":
                pass
                # print('考试名称：%s;\n课程名: %s;\n班级: %s;\n老师: %s ;\n时间 : %s ;\n地点 ：%s ;\n\n\n' % (i['ksmc'], i['kcmc'], i['bj'], i['jsxx'], i['kssj'], i['cdmc']))
        info = []
        for i in ksxxList:
            info.append({
                'kcmc': i['kcmc'],
                'cdmc': i['cdmc'],
                'kssj': i['kssj'],
                'jsxx': i['jsxx']
            })
        if ksxxList:
            return info
        else:
            return self.getExamTime()

    # 课表
    def getClassTable(self):
        if not self.isLogin:
            return None
        classTableUrl = self.baseUrl + '/jwglxt/kbcx/xskbcx_cxXskb.html?gnmkdm=N2151&layout=default&su=' + self.__username
        xqm = [3, 12, 16][int(self.__xqm) - 1]
        datas = {
            'xnm': self.__xnm,
            'xqm': xqm,
            '_search': False,
            'nd': self.nowTime,
            'queryModel.showCount': 15,
            'queryModel.currentPage': 1,
            'queryModel.sortName': ' ',
            'queryModel.sortOrder': 'asc',
            'time': 1
        }
        head = self.header
        head['X-Requested-With'] = 'XMLHttpRequest'
        head['Referer'] = classTableUrl
        head['Accept'] = 'application/json, text/javascript, */*; q=0.01'
        head['Content-Type'] = 'application/x-www-form-urlencoded;charset=UTF-8'
        if 'Upgrade-Insecure-Requests' in head:
            head.pop('Upgrade-Insecure-Requests')
        rep = self.__req.post(self.baseUrl + '/jwglxt/kbcx/xskbcx_cxXsKb.html?gnmkdm=N2151', data=datas, headers=head)

        return json.loads(rep.text)

    # 获取学期
    @staticmethod
    def getTerm():
        now = datetime.datetime.today()
        Year = int(datetime.datetime.strftime(now, '%Y'))
        Month = int(datetime.datetime.strftime(now, '%m'))
        Term = 0

        # 第一个学期
        if 9 <= Month <= 12:
            Term = 1
        if Month == 1:
            Year -= 1
            Term = 1
        if 2 <= Month <= 6:
            Year -= 1
            Term = 2
        if 7 <= Month <= 8:
            Year -= 1
            Term = 3

        return Year, Term

    # 获取本学期课程名字列表
    def getCourse(self):
        data = self.getClassTable()
        data = data["kbList"]
        temp = []
        for i in range(len(data)):
            dic = {"courseName": data[i]["kcmc"], "courseTeacher": data[i]["xm"]}
            temp.append(dic)

        return temp

    # 获取考试时间对外接口封装
    def getExam(self):
        self.login()
        if not self.isLogin:
            return {
                "data":[],
                "msg":"登录失败请检查账号密码是否正确",
                "status":False
            }

        data=self.getExamTime()

        return {
            "data":data,
            "msg":"获取考试成功",
            "status":True
        }

if __name__ == "__main__":
    pass
