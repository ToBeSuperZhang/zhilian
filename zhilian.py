import json
import random
from time import sleep
import requests
import re
from lxml import etree
import re


# 解析网页
def parse_url(url, cookies, headers):
    response = requests.get(url=url, cookies=cookies, headers=headers)

    return response

# 智联的json加密是很坑的json
def get_json(response, cookies, headers2):

    html = etree.HTML(response.text)
    # 获取简历信息列表
    datas = html.xpath("//div[@class='resumes-list'][last()]//table/tbody/tr[@valign='middle']")

    # 获取总页面数
    page_num = int(html.xpath("//span[@id='rd-resumelist-pageNum']/text()")[0].split('/')[1])
    # 获取js链接特殊属性
    for data in datas:
        print('----------------------')

        # 截取js链接发现不同的简历,不同的地方只有两个一个是resumeurlpart,一个是k,
        json_k = data.xpath("./td[2]/a[1]/@k")[0]
        json_n = data.xpath("./td[2]/a[1]/@resumeurlpart")[0]
        # 你以为t 一样就不要获取了? too young! 你每次点搜索他的数值都不一样! 虽然整个页面这个值都一样!灯下黑!!目前猜测是跟时间有关
        json_t = data.xpath("./td[2]/a[1]/@t")[0]

        # 获取js 链接,数据真实地址
        json_url = 'http://ihr.zhaopin.com/resumesearch/getresumedetial.do?access_token=074522a89efe42c49fabb1fa4c467d69' \
                   '&resumeNo=%s&searchresume=1&resumeSource=1&keyword=python&t=%s&k' \
                   '=%s&v=0&version=3&openFrom=1' % (json_n, json_t, json_k)

        #获取数据, 得到的是json值
        json_data2 = requests.get(url=json_url, cookies=cookies, headers=headers2)

        # 将json进行转换
        data_list = json.loads(json_data2.text)

        # 获取信息
        get_info(data_list)

        # 等待预防反爬, 推测2s 加
        sleep(random.random() + random.randint(2, 5))
    return page_num


def get_info(data_list):
    # 简历个空字典等待接受
    info = {}

    # 这个没坑
    info['name'] = data_list['data']['userDetials']['userName']
    # 这个没坑
    info['email'] = data_list['data']['userDetials']['email']
    # 这个也没坑 正常操作就好
    info['birthStr'] = data_list['data']['userDetials']['birthStr']
    info['old'] = data_list['data']['userDetials']['birthYear']
    info['birthMonth'] = data_list['data']['userDetials']['birthMonth']
    info['birthDay'] = data_list['data']['userDetials']['birthDay']
    info['maritalStatus'] = data_list['data']['userDetials']['maritalStatus']  # 2 为已婚
    info['mobilePhone'] = data_list['data']['userDetials']['mobilePhone']
    info['workYearsRangeId'] = data_list['data']['userDetials']['workYearsRangeId']

    CommentTitle = {}
    # 坑在这里....你在网后一步你会发现怎么都获取不了, 一直提示NoType类型,因为这个东西后面跟着的是字符串.......那么长要瞎了
    com = json.loads(data_list['data']['detialJSonStr'])
    CommentTitle['title'] = com['CommentTitle']
    CommentTitle['content'] = com['CommentContent']
    # 不想注释了, 本来爬了新浪新闻的准备放上来,结果上传github的时候上传失败 我又手贱把历史记录删了.心好累就这样吧......
    WorkExperience = {}
    WorkExperience_list = com['WorkExperience']
    WorkExperience['DateStart'] = [workexperience['DateStart'] for workexperience in WorkExperience_list]
    WorkExperience['DateEnd'] = [workexperience['DateEnd'] for workexperience in WorkExperience_list]
    WorkExperience['JobTitle'] = [''.join(workexperience['JobTitle']).replace('/','').replace('|','').replace('\\','') for
                                  workexperience in
                                  WorkExperience_list]
    WorkExperience['Salary'] = [workexperience['Salary'] for workexperience in WorkExperience_list]
    WorkExperience['WorkDescription'] = [workexperience['WorkDescription'] for workexperience in WorkExperience_list]
    WorkExperience['CompanyName'] = [workexperience['CompanyName'] for workexperience in WorkExperience_list]

    Project = {}
    Project['ProjectName'] = [pro['ProjectName'] for pro in com['ProjectExperience']]
    Project['ProjectResponsibility'] = [pro['ProjectResponsibility'] for pro in com['ProjectExperience']]
    Project['SoftwareEntironment'] = [pro['SoftwareEntironment'] for pro in com['ProjectExperience']]

    download(info, CommentTitle, WorkExperience, Project)


def download(info, CommentTitle, WorkExperience, Project):
    text_name = './简历/'+str(info['name']) + ''.join(WorkExperience['JobTitle']).replace(' ','')[:20] + \
                '.txt'
    with open(text_name, 'wb') as f:
        info_str = ''
        for key in info:
            info_str += key + ':' + str(info[str(key)]) + '\n'
        CommentTitle_str = ''
        for key in CommentTitle:
            CommentTitle_str += key + ':' + str(CommentTitle[str(key)]) + '\n'
        WorkExperience_str = ''
        for key in WorkExperience:
            for data in WorkExperience[str(key)]:
                WorkExperience_str += key + ':' + data + '\n'
        Project_str = ''
        for key in Project:
            for data in Project[str(key)]:
                Project_str += key + ':' + data + '\n'
        f.write((info_str + '\n' + CommentTitle_str + '\n' + WorkExperience_str + '\n' + Project_str).encode('utf-8'))
        f.flush()




if __name__ == '__main__':
    # 本爬虫代码爬取的只是python简历,原因也是因为想多了解一下行业动态
    #  我使用的是企业版账号 可以获取简历更详细的信息,因为智联不封ip 所以就不想设ip代理池.
    # 智联有稍微麻烦一点的反爬措施:登录头信息和搜索页面头信息有细微差别,至少需要设置两个header才能成功获取到搜索页面信息
    headers = {
        'Host': "ihrsearch.zhaopin.com",
        'Connection': "keep-alive",
        'Upgrade-Insecure-Requests': "1",
        'User-Agent': "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.186 Safari/537.36",
        'Accept': "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
        'Referer': "https://ihrsearch.zhaopin.com/home/SearchByCustom",
        'Accept-Language': "zh-CN,zh;q=0.9",
        'Cache-Control': "no-cache",
        'Postman-Token': "44090375-05b8-4f3c-a7e8-a957bd9242d8",
        # 'Referer': 'http://ihr.zhaopin.com/resume/details/?resumeNo=F(bc3frWinKrIxuR8dgh4w_1_1&searchresume=1&resumeSource=1&keyword=python&t=1523168064306&k=CAD90FB56DC3D1BFF88520B65E89F7C8&v=1&version=3&openFrom=1'
    }
    headers2 = {
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Accept-Encoding': 'gzip, deflate',
        'Accept-Language': 'zh-CN,zh;q=0.9',
        'Connection': 'keep-alive',
        'Host': 'ihr.zhaopin.com',
        'Referer': '*',
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.186 '
                      'Safari/537.36',
        'X-Requested-With': 'XMLHttpRequest'
    }

    cookies = \
        {'adfbid2': '0',
         'NTKF_T2D_CLIENTID': 'guestE1EF2D24-80B7-7F68-0058-99E04A9B79AE',
         'sts_deviceid': '16299e04f3bf6-061562b4d7483-3e3d5f01-1327104-16299e04f3c619',
         'Home_ResultForCustom_orderBy': 'DATE_MODIFIED%2C1',
         'renderVersion': '3',
         '__utmz': '269921210.1523167965.12.3.utmcsr=passport.zhaopin.com|utmccn=(referral)|utmcmd=referral|utmcct=/org/login',
         '__utma': '269921210.776877629.1520218609.1523191639.1523236222.17',
         '__utmt': '1',
         'Hm_lvt_38ba284938d5eddca645bb5e02a02006': '1523044969,1523055396,1523179590,1523236222',
         '_jzqckmp': '1',
         'LastCity': '%e6%b7%b1%e5%9c%b3',
         'LastCity%5Fid': '765',
         '__xsptplusUT_30': '1',
         '__zpWAM': '1522999937641.369493.1523167293.1523236241.8',
         '__zpWAMs1': '1',
         'urlfrom': '121120123',
         'urlfrom2': '121120123',
         'adfbid': '0',
         'adfcid': '360so_pz_zbt_zhilianzhaopin1',
         'adfcid2': '360so_pz_zbt_zhilianzhaopin1',
         'dywea': '95841923.3311331951592837600.1520218609.1523236222.1523236355.31',
         'dywec': '95841923',
         'dywez': '95841923.1523236355.31.7.dywecsr=zhaopin.com|dyweccn=(referral)|dywecmd=referral|dywectr=undefined|dywecct=/',
         '__utmc': '269921210',
         '__xsptplus30': '30.7.1523236236.1523236356.2%234%7C%7C%7C%7C%7C%23%233PjN0sMcV94YGXaDpYobuPdlKzgJ8WVk%23',
         '_jzqa': '1.2131717558650616800.1520218646.1523236223.1523236357.20',
         '_jzqc': '1',
         '_jzqx': '1.1520218646.1523236357.2.jzqsr=jobs%2Ezhaopin%2Ecom|jzqct=/shenzhen/sj506/ju_python/.jzqsr=zhaopin%2Ecom|jzqct=/',
         '_jzqb': '1.1.10.1523236357.1',
         'JsOrglogin': '2071680368',
         'at': '7c1aa039c2dd49b3bdb5ecdff0be913d',
         'Token': '7c1aa039c2dd49b3bdb5ecdff0be913d',
         'rt': 'a81ef4c1f83740ce968f57575a7c4c33',
         'RDsUserInfo': '376436655a6652665d7755754c6f4f7549695364406555665f6628772b75446f0075086956644a6550665766577755754d6f4a750b69046449653466306659775475426f3b753d695f6446655f66536657775675496f4d754a69596433653366596650774875406f597540695864436553665f6625772975446f49754269376433655a662e6629775c75496f4c754f69526443655566566656775e752c6f2d7544695364446557665f6637772c75446f4b7542690',
         'uiioit': '213671340f69436b546a587941644574063505325b75596d51683b742073493601340a69426b5e6a5b794464477405350f328',
         'zp-route-meta': 'uid=690560122,orgid=48733043',
         'nTalk_CACHE_DATA': '{uid:kf_9051_ISME9754_48733043,tid:1523236449605703}',
         'adShrink': '1',
         'searchVersion': '',
         'tonewpage': '0',
         '__utmb': '269921210.29.9.1523236468812',
         'dyweb': '95841923.14.9.1523236468804', }

    # 获取登录首页信息
    url = 'https://ihrsearch.zhaopin.com/Home/ResultForCustom?SF_1_1_1=python&SF_1_1_6=765&SF_1_1_18=765&orderBy=DATE_MODIFIED,1&SF_1_1_27=0&exclude=1'
    response = parse_url(url, cookies, headers)

    # 获取登录状态码
    print(response.status_code)

    # 获取总页面数
    page_num = get_json(response, cookies, headers2)

    # 创建一个空列表准备接受url
    url_list=[]
    print('-------第1页结束'-------)
    for i in range(2,page_num+1):
        print('-----------------------')
        print('-------第'+str(i)+'页结束-------')

        # 搜索页面链接
        url = 'https://ihrsearch.zhaopin.com/Home/ResultForCustom?SF_1_1_1=python&SF_1_1_6=765&SF_1_1_18=765&orderBy' \
              '=DATE_MODIFIED,1&SF_1_1_27=0&exclude=1&pageIndex='+str(i)

        # 解析简历详情页面
        response = parse_url(url, cookies, headers)

        # 这里json是个坑,智联简历详细数据是通过js,而js的网址...你以为是要传两个参,后面你会发现是3个,传递的,js里面的json非常.....坑
        page_num = get_json(response, cookies, headers2)


    # print(page_num)
