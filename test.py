# coding: utf-8
import random
import pymongo
import requests
from lxml import html
from multiprocessing.dummy import Pool
from pymongo.errors import DuplicateKeyError

client = pymongo.MongoClient('localhost', 27017)
zoomeye = client['zoomeye']
db_web = zoomeye['web']
db_web.ensure_index('url', unique=True)

user_agents = [
    'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:23.0) Gecko/20130406 Firefox/23.0',
    'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:18.0) Gecko/20100101 Firefox/18.0',
    'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11',
    'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/28.0.1468.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/43.0.2357.130 Safari/537.36',
]


def get_headers():
    headers = {
        'User-Agent': random.choice(user_agents)
    }
    return headers


def get_head(domain='', times=0):
    if times > 1:
        return
    try:
        url = 'http://www.' + domain + '.com'
        resp = requests.get(url, headers=get_headers(), timeout=5, stream=True)
        ct = resp.headers.get('Content-Type')
        th = False
        ed = ''
        meta_data = {}
        if ct:
            for c in ct.split('; '):
                if 'charset' in c:
                    ed = c.split('=')[1].lower()
                if 'text/html' in c:
                    th = True
        if not ed:
            if th:
                tree = html.fromstring(resp.text)
                tmp = tree.xpath('//meta//@charset')
                ed = tmp[0] if tmp else ''
                if not ed:
                    tmp = tree.xpath('//meta[@http-equiv="Content-Type"]')
                    if tmp:
                        for c in tmp[0].get('content').split('; '):
                            if 'charset' in c:
                                ed = c.split('=')[1].lower()
        resp.encoding = ed if ed else 'iso8859-1'
        if th:
            tree = html.fromstring(resp.text)
            meta = tree.xpath('//meta[@name]')
            if meta:
                for m in meta:
                    meta_data[m.get('name')] = m.get('content')
            title = tree.xpath('//title')
            if title:
                meta_data['title'] = title[0].text
        web_data = dict(dict(resp.headers), **meta_data)
        try:
            web_data['url'] = url
            db_web.insert_one(web_data)
            print(url)
        except DuplicateKeyError:
            print(url + ' 重复存入')
    except requests.exceptions.ConnectionError:
        pass
    except requests.exceptions.ReadTimeout:
        get_head(domain, times + 1)
    except Exception as ex:
        print(ex.args[0])


def ten_to_thirty_six(num):
    loop = '0123456789abcdefghijklmnopqrstuvwxyz'
    a = []
    while num != 0:
        a.append(loop[num % 36])
        num = int(num / 36)
    a.reverse()
    out = ''.join(a)
    return out


def begin(num=10000000):
    start = 1
    end = 300
    while end < num:
        print(start)
        pool = Pool(5)
        for i in range(start, end):
            domain = str(ten_to_thirty_six(i))
            pool.apply_async(get_head, (domain,))

        pool.close()
        pool.join()

        start = end
        end += 300


if __name__ == "__main__":
    begin()
