#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
使用urllib库和正则表达式爬取http://odf2.worldcurling.co/data/，得到冰壶比赛的pdf场记图，存放在当前目录下
选项：自定义参数是比赛名称
（'CU_WJCC2016P',
 'CU_WMCC2016P',
 'CU_WMDCC2016P',
 'CU_WSCC2016P',
 'CU_WWhCC2016P',
 'CUR_1819_CWC_1P',
 'CUR_1819_CWC_1T',
 'CUR_1819_CWC_2P',
 'CUR_1819_CWC_3P',
 'CUR_1819_CWC_4P',
 'CUR_1819_CWC_4T',
 'CUR_1819_WMxCCP',
 'CUR_ECC2016P',
 'CUR_ECCA2017P',
 'CUR_ECCA2018P',
 'CUR_ECCB2016P',
 'CUR_ECCB2017P',
 'CUR_ECCB2018P',
 'CUR_ECCC2017P',
 'CUR_ECCC2018P',
 'CUR_ECCC2019P',
 'CUR_EYOF2019P',
 'CUR_OQE2017P',
 'CUR_PACC2016P',
 'CUR_PACC2017B',
 'CUR_PACC2017P',
 'CUR_PACC2018P',
 'CUR_WJBCC2017P',
 'CUR_WJBCC2018P',
 'CUR_WJBCC2019P',
 'CUR_WJCC2017P',
 'CUR_WJCC2017T',
 'CUR_WJCC2018P',
 'CUR_WJCC2019P',
 'CUR_WMCC2017P',
 'CUR_WMCC2018P',
 'CUR_WMCC2019P',
 'CUR_WMDCC2017P',
 'CUR_WMDCC2018P',
 'CUR_WMDCC2019P',
 'CUR_WMxCC2016P',
 'CUR_WMxCC2017P',
 'CUR_WQE2019P',
 'CUR_WSCC2017P',
 'CUR_WSCC2018P',
 'CUR_WSCC2019P',
 'CUR_WWCC2017P',
 'CUR_WWCC2018P',
 'CUR_WWCC2019P',
 'CUR_WWhBCC2018P',
 'CUR_WWhCC2017P',
 'CUR_WWhCC2019P',
 'CUR_WWhCCB2016P',
 'OWG2018P',
 'OWG2018T',
 'PWG2018P',
 'UNKNOWN',
 'UNKNOWNP',
 'UNKNOWNT',
 'WU2019P',
 'WUNI2017P',
 'WYOG2016P',
 'WYOG2016T')
 默认将爬取所有赛事

 time.sleep请根据实际网络情况进行调整，默认打开日志文件，请留意

"""

import sys
import urllib.request
import re
import time
import os


# 自定义参数：爬取指定单场比赛，默认爬取所有
event_directory_list = []
if len(sys.argv) > 1:
    event_directory_list.append("/data/"+ sys.argv[1] + "/")

else:

    response = urllib.request.urlopen("http://odf2.worldcurling.co/data")
    events_html = response.read()
    
    # 正则表达式查找用双引号引起来的字符串，以/data开头，最大字符数不超过20

    event_directory_list = re.findall('"/data/.{0,20}?/"', events_html.decode('utf-8'))

# 去除路径上的引号
for i in range(len(event_directory_list)):
    event_directory_list[i] = event_directory_list[i].strip("\"")


# 获取到比赛的列表:event_directory,接下来遍历查看每场赛是否含有shot-by-shot summaries这个pdf文件，然后在本地同名目录保存它们。

# 在运行过程中由于网络问题可能导致程序崩溃，请打开check_log_file，并手动添加日志文件，实现在上一次断开的地方继续运行程序。

# check_log_file = False

# 如果要使用日志文件，请注释掉上行，并需要在data_download.log文件中手动添加已爬取过的赛事名称。
check_log_file = True
log_file = open("data_download.log", "r").read()

# 爬取男队、女队比赛数据。
game_types = ["Men\'s_Teams", "Women\'s_Teams"]
for event_dir in event_directory_list:

    # 检查此赛事是否在上一个日志文件中。
    if check_log_file and (event_dir in log_file):
        print("Skipping previously handled event directory: " + event_dir, flush = True)
        continue

    
    # 设置缓冲，减少请求失败概率。
    time.sleep(3)

    # 请求data下的赛事名称目录。
    req_string = "http://odf2.worldcurling.co" + event_dir
    print("Searching " + req_string, flush = True)
    response = urllib.request.urlopen(req_string)
    types_html = response.read()

    # 遍历比赛类型gametype。
    for gt in game_types:

        # 如果存在该比赛类型目录，则请求该目录的下一级。
        if re.search(gt, types_html.decode('utf-8')):

            time.sleep(3)

            # 请求目录

            req_string = "http://odf2.worldcurling.co" + event_dir + gt + "/"
            print("Searching " + req_string, flush = True)           
            response = urllib.request.urlopen(req_string)

            sessions_html = response.read()


            # 现在，此页面上的子目录是包含逐个镜头摘要的子目录。 因此获得要遍历的子目录数组。
            session_dirs = re.findall('"' + event_dir + gt + '/.*?/"',sessions_html.decode('utf-8'))

            # #session_dirs现在应包含完整路径。遍历它们，请求每个页面，获取
            #逐个镜头摘要列表，并将其下载到从当前工作目录（相同的结构）。
            for path in session_dirs:

                time.sleep(2)

                # 去除路径上的多余引号
                path = path.strip("\"")
                
                req_string = "http://odf2.worldcurling.co" + path
                print("Searching " + req_string, flush = True)
                response = urllib.request.urlopen(req_string)
                pdfs_html = response.read()

                summary_paths = re.findall('"' + path + '.{0,20}?_Shot_by_Shot_.*?.pdf"',pdfs_html.decode('utf-8'))
                

                """
                如果summary_paths不为空，保存这些文件，验证（或创建）
                目录结构，通过在正斜杠上分割此字符串来获取完整的目录结构。
                去除所有前导和尾随的正斜杠，因此此列表仅包含各种名称，并且不包含空字符串。 
                dir_path存储我们深入目录结构时的路径。
                
                """
                if(len(summary_paths) == 0):
                    print("No summary files found.  Switching to new directory.", flush = True)
                    continue
                else:
                    print(str(len(summary_paths)) + " summary files found. Saving...", flush = True)


                dir_list = path.strip("/").split("/")
                dir_path = ""
                for dir_name in dir_list:
                    if not os.path.exists(dir_path + dir_name):
                        os.mkdir(dir_path + dir_name)

                    dir_path += dir_name + "/"

                
                # 遍历summary路径并将每个文件保存到本地。
                for summary in summary_paths:

                    summary = summary.strip("\"")

                    time.sleep(2)
                    response = urllib.request.urlopen("http://odf2.worldcurling.co" + summary)
                    pdf_file = response.read()

                    out_file = open(summary.strip("/"), "wb")
                    out_file.write(pdf_file)
                    out_file.close()

print('all done')
