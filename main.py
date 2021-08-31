#!/usr/bin/env python3
# -*- coding=utf-8 -*-
# @File     : main.py
# @Time     : 2021/8/30 15:40
# @Author   : NagisaCo
import asyncio
import json
import aiohttp
import os
import time


class Ana(object):
    def __init__(self, data, file):
        self.data = data
        self.file = file
        self.csv = ""

    def __ana_one(self, _time, _data):
        for item in _data:
            if not '00' <= _time[8:10] <= '05':
                t = f'{_time[0:4]}-{_time[4:6]}-{_time[6:8]} {_time[8:10]}:00'
                csv_line = item + ',' + str(_data[item].get('hot')) + ',' + t + '\n'
                self.csv += csv_line

    def run(self):
        for item in self.data:
            if 202106000000 < int(item) < 202107000000:
                print(item)
                self.__ana_one(item, self.data.get(item))

        with open(self.file, 'w', encoding='utf-8') as f:
            f.write('name,value,date\n')
            f.writelines(self.csv)


class Downloader(object):
    def __init__(self, path):
        self.session = None
        self.path = path
        self.log_list = []
        self.data = {}

    def run(self):
        self.__get_log()
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.__fetch_all())
        return self.data

    async def __fetch(self, item):
        url = f'https://cdn.jsdelivr.net/gh/Arrackisarookie/weibo-hot-search@{item.get("commit")}/raw/{item.get("date")[0:8]}.json'
        print(f'[{item.get("commit")}]: Fetching')
        response = await self.session.get(url)
        content = await response.read()
        data = json.loads(content.decode(encoding='UTF-8'))

        result = {}

        for _ in data:
            result.update({_: data.get(_)})
            if len(result) >= 20:
                break

        print(f'[{item.get("commit")}]: Finish')
        await asyncio.sleep(0.05)
        try:
            return {item.get("date"): result}
        except Exception:
            return None

    async def __fetch_all(self):
        async with aiohttp.ClientSession() as session:
            self.session = session
            tasks = []
            for item in self.log_list:
                if item.get("date") > '202107000000':
                    tasks.append(asyncio.create_task(self.__fetch(item)))
            done, pendding = await asyncio.wait(tasks)

        for item in done:
            result = item.result()
            if result is not None:
                self.data.update(result)

    def __get_log(self):
        os.popen(f"cd /d {self.path} && git pull")
        git_log = os.popen(f"cd /d {self.path} && git --no-pager log").read()
        beginTag = False
        goodLine = {0: "", 1: "", 2: "", 3: "", 4: ""}
        lines = git_log.split('\n')
        for line in lines:
            if len(line) <= 2:
                continue
            if line.startswith("commit"):
                beginTag = True
                goodLine[0] = line[6:]
                continue
            if beginTag:
                if line.startswith("Merge: "):
                    goodLine[1] = line[7:]
                elif line.startswith("Author: "):
                    goodLine[2] = line[8:]
                elif line.startswith("Date: "):
                    goodLine[3] = line[6:]
                else:
                    goodLine[4] = line
                    beginTag = False
                    self.log_list.append({
                        'commit': goodLine[0].strip(),
                        'date': time.strftime('%Y%m%d%H%M',
                                              time.strptime(goodLine[3].strip(), '%a %b %d %H:%M:%S %Y %z'))
                    })
                    goodLine = {0: "", 1: "", 2: "", 3: "", 4: ""}


if __name__ == "__main__":
    # down = Downloader(r'D:\Work\Github\weibo-hot-search')
    # data = down.run()
    #
    # data_sort = {}
    #
    # for i in sorted(data, reverse=True):
    #     data_sort.update({i: data.get(i)})
    #
    # with open('data_sorted.json', 'w', encoding="utf-8") as f:
    #     json.dump(data_sort, f, ensure_ascii=False)

    with open('data_sorted.json', 'r', encoding='utf-8') as f:
        data = json.load(f)

    data_sort = {}

    for i in sorted(data):
        data_sort.update({i: data.get(i)})

    ana = Ana(data_sort, 'data_6.csv')
    ana.run()
