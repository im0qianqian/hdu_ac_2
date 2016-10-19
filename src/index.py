# -*- coding:utf-8 -*-  
import urllib  
import urllib2
import cookielib
from bs4 import BeautifulSoup
import re
import time
import sys
import getpass
import code
import requests
import threading

# 用户信息
qian_id = ''
qian_pwd = ''

# 题目信息
start_pro = 1000
end_pro = 5932

# 其他信息
headers = {
    'User-Agent':'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.154 Safari/537.36 LBBROWSER'
    }

# 语言与post对应
language = {'g++':'0',
            'gcc':'1',
            'c++':'2',
            'c':'3',
            'pascal':'4',
            'java':'5',
            'c#':'6',
            'cpp':'0'
    }


def login():
    global qian_id, qian_pwd, headers  # 声明是全局变量
    
    qian_id = raw_input('Please enter your username: ')
    qian_pwd = getpass.getpass('Please enter your password: ')
    
    # post数据接收和处理的页面（我们要向这个页面发送我们构造的Post数据）  
    posturl = 'http://acm.hdu.edu.cn/userloginex.php?action=login'

    # 设置一个cookie处理器，它负责从服务器下载cookie到本地，并且在发送请求时带上本地的cookie  
    c = cookielib.LWPCookieJar()
    opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(c))

    # 构造Post数据
    postData = {'username' : qian_id.strip(),
                'userpass' : qian_pwd.strip()
    }
    
    # 需要给Post数据编码  
    postData = urllib.urlencode(postData)
    
    # 通过urllib2提供的request方法来向指定Url发送我们构造的数据，并完成登录过程  
    request = urllib2.Request(posturl, postData, headers)
    loginin = opener.open(request).read()
    
    if(loginin.find('No such user or wrong password.') != -1):
        print 'No such user or wrong password.'
        exit()
    
    headers['Cookie'] = re.search('PHPSESSID=[A-Za-z0-9_]*', str(c)).group()  # 提取cookie
    print 'Login success'



def status(pro_id):
    global qian_id, headers
    status_url = 'http://acm.hdu.edu.cn/status.php?user=' + qian_id
    
    req = urllib2.Request(status_url, urllib.urlencode({}), headers)
    
    while(True):
        time.sleep(1)  # 每次抓取结果间歇1s
        
        html = urllib2.urlopen(req).read()
        soup = BeautifulSoup(html, "lxml")  # 美味的汤
        for i in soup.table.find_all('table')[-2].find_all('tr'):
            ans = i.find_all('td')
            if(ans[3].string == pro_id):
                dan = ans[2].string
                if(dan != 'Queuing' and dan != 'Compiling'):
                    print dan
                    return
                break

    
    
    
    
def find_the_code(url, pro_id):  # 寻找页面内代码并提交
    global headers
    
    # POST
    submit_url = 'http://acm.hdu.edu.cn/submit.php?action=submit'
    
    sesson = requests.Session()
    sesson.headers.update(headers)
    
    try:
        html_code = sesson.get(url).text
        
        soup = BeautifulSoup(html_code, "lxml")  # 美味的汤

        for i in soup.find_all('pre'):
            code = i.string  # 最终代码
            
            if code == None:
                return
            
            try:
                if(code.find('main') != -1):  # 如果代码中有main函数
                    # POST数据
                    post_data = {
                        'problemid': pro_id,
                        'usercode' : code,
                        'language' : language[i.get('class')[0]]
                        }
                    # 需要给Post数据编码  
                    postData = urllib.urlencode(post_data)
                    request = urllib2.Request(submit_url, postData, headers)
                    print 'post ' + pro_id
                    urllib2.urlopen(request)
                    # status(pro_id)
                    print '------------------ ' + pro_id + ' Submit successfully\n'
            except KeyError, TypeError:
                print 'KeyError'
                
    except urllib2.URLError :  # 异常情况
        print 'URLError'
    


def from_bing(pro_id):  # 从必应获取链接
    find_path = 'http://cn.bing.com/search?q=HDU+' + pro_id + '+CSDN'  # 必应
    bing_code = urllib2.urlopen(find_path).read()
    find_code_url = re.findall('href=\"(http://blog.csdn[^\\s\"]+)\"', bing_code)
    return find_code_url[:2]


def from_baidu(pro_id):
    find_path = 'http://www.baidu.com/s?&wd=HDU%20' + pro_id + '%20CSDN'  # 百度
    baidu_code = urllib2.urlopen(find_path).read()
    find_code_url = re.findall('(http://www.baidu.com/link\?url=[^\"]*)', baidu_code)
    return find_code_url[:3]
    
    
def find_the_code_path(pro_id, url_path):  # 搜索代码路径
    print 'start ' + pro_id
    find_code_url = url_path(pro_id)
    for i in find_code_url:
        print 'find in ' + i
        find_the_code(i, pro_id)
        time.sleep(5)  # 休息5s
    

def judgeisac(pro_id):  # 查询是否已经被我AC
    global headers, qian_id
    html = open('aclog.txt').read()
    if(html.find(pro_id) != -1):
        return False
    return True


def start():  # 单线程
    for i in range(start_pro, end_pro):
        pro_id = str(i)
        if(judgeisac(pro_id) == True):
            find_the_code_path(pro_id, from_baidu)  # 从百度
            find_the_code_path(pro_id, from_bing)  # 从必应
        


def start2():  # 多线程
    for i in range(start_pro, end_pro, 3):
        threads = []
        for j in range(i, i + 3):
            pro_id = str(j)
            if(judgeisac(pro_id) == True or True):
                threads.append(threading.Thread(target=find_the_code_path, args=(pro_id, from_baidu)))  # 从百度
                threads.append(threading.Thread(target=find_the_code_path, args=(pro_id, from_bing)))  # 从必应
        print threads
        for t in threads:
            t.setDaemon(True)
            t.start()
        t.join()
    print "All over"




if __name__ == '__main__':
    reload(sys)
    sys.setdefaultencoding('utf-8')
    login()
    start2()
