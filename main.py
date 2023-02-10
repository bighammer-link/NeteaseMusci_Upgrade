import requests
import random
import json
import qrcode     # 第三方二维码生成库
import time


#下面是需要填写的配置内容,具体怎么填写，请看readme
api = ''
#server酱紫的推送方式
sckey = ''
#歌单id
user_sl_id = ''

#---------------------------------分界线-----------------------------------------------------------------
user_songslist=[]
user_songsformlist=[]
grade = [10, 40, 70, 130, 200, 400, 1000, 3000, 8000, 20000]# 此处是网易云不同等级对应的歌曲数量
session = requests.session()
'''
该函数相当于重新定义了request.post请求
该方法会带着用户cookie发送请求
url:完整的URL路径
dataJson:要以post方式发送的数据
'''
def getResponse(url, dataJson, user_cookies):
    response = session.post(url=url, data=dataJson, headers={'Content-Type': 'application/x-www-form-urlencoded'})#,cookies=user_cookies
    return response


'''
登录
这是使用二维码登录
'''
def code_login():
    url = api + '/login/qr/key'
    key_info = json.loads(requests.post(url=url).text)
    key = key_info['data']['unikey']

    url_code = api + '/login/qr/create?key=' + str(key)
    code_data = json.loads(requests.post(url=url_code).text)['data']['qrurl']

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4
    )
    # 传入数据
    qr.add_data(code_data)
    qr.make(fit=True)
    # 生成二维码
    img = qr.make_image()
    # 保存二维码
    img.save('code.jpg')
    print('正在生成二维码,二维码出现后请在一分钟内完成扫码登录')
    time.sleep(5)
    # 展示二维码
    qr.print_ascii() # 如果是部署在本地电脑将此行注释掉，下面这一行取消注释
    # img.show()       #
    time.sleep(60)
    print('开始验证登录状态')
    url_check = api + '/login/qr/check?key=' + str(key)
    response = session.post(url_check)
    result = json.loads(response.text)

    time.sleep(5)
    while True:
        if result['code'] == 800:
            print("二维码过期")
            time.sleep(2)
        elif result['code'] == 801:
            print('等待扫码,那么墨迹的吗')
            time.sleep(2)
        elif result['code'] == 802:
            print('待确认')
            time.sleep(2)
        else:
            if result['code'] == 803:
                print('登录成功')
                info_url = api + '/user/account'
                info_response = session.post(info_url)
                info_result = json.loads(info_response.text)
                # print(info_result)
                user_uid = info_result['account']['id']
                user_cookies = info_response.cookies
                # print(user_cookies)
                return user_cookies, user_uid
            else:
                print('登陆失败')
                break

'''
 每日签到
'''
def daily_check(user_cookies):
    check_url = api +'/daily_signin'
    response = getResponse(check_url, {"r" : random.random()},user_cookies)
    data = json.loads(response.text)
    if data['code'] == 200:
        print("签到成功")

    else:
        print('重复签到')

'''
进行云贝中心签到
'''
def yunbei_sign(user_cookies):
    sign_url = api + '/yunbei/sign'
    response = getResponse(sign_url, {"r" : random.random()},user_cookies)
    data = json.loads(response.text)
    if data['code'] == 200:
        print("云贝签到成功，获得{}云贝".format(data['point']))

    else:
        print('重复签到')

'''
获取用户信息
'''
def get_uer(user_uid, user_cookies):
    url = api + '/user/detail?uid=' + str(user_uid)
    response = getResponse(url, {"r": random.random()}, user_cookies)
    result = json.loads(response.text)
    # print(result)
    user_level = result['level']
    user_listensongs = result['listenSongs']
    print('获取用户信息成功')
    return user_level,user_listensongs

'''
获取歌单的所有歌曲
'''
def get_songlist(user_sl_id,user_cookies):
    url = api + "/playlist/track/all?limit=300&offset=0&id="+str(user_sl_id)
    response = getResponse(url, {"r" : random.random()}, user_cookies)
    result = json.loads(response.text)
    # print(result)
    for i in result['songs']:
        user_songslist.append(i['id'])
        user_songsformlist.append(i['al']['id'])
    print('获取歌单列表id成功')

'''
进行听歌打卡
'''
def check(user_level,user_listensongs,user_cookies):
    num = 0
    print('当前等级是{}'.format(user_level))
    print('从歌单第一首歌曲开始打卡。。。')

    for i in range(300):
        url = api + '/scrobble?id=' + str(user_songslist[i])+'&sourceid='+str(user_songsformlist[i])+'&time=70'
        response = getResponse(url, {"r" : random.random()},user_cookies)
        num += 1
        sleep_time = 70 + random.randint(3,10)
        time.sleep(sleep_time)
        print('已听完{}首歌，即将进行下一首。还需听{}首歌，即可升至{}级'.
                format(num, grade[int(user_level)]-(user_listensongs+num), user_level+1))

    print('恭喜！今日已经听歌三百首，完成任务')



'''
使用server酱推送
'''
def server_push(user_level,user_listensongs):
    content = '恭喜！今日已经听歌三百首，完成任务,还需{}首歌，即可升至{}级'.format(grade[int(user_level)] - user_listensongs - 300,user_level + 1)
    print(content)
    url =  "https://sctapi.ftqq.com/{}.send?title={}&desp={}".format(sckey, "网易云听歌任务",content)
    requests.post(url)
    print('推送完成')

'''主程序'''
def main():
    # 首先进行二维码登录
    user_cookies, user_uid = code_login()
    daily_check(user_cookies)
    yunbei_sign(user_cookies)
    user_level, user_listensongs = get_uer(user_uid, user_cookies)
    get_songlist(user_sl_id, user_cookies)
    
    check(user_level, user_listensongs, user_cookies)
    if sckey!='':
      server_push(user_level, user_listensongs)
    

if __name__ == '__main__':
    main()
