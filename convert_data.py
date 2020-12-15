#!/usr/bin/env python

# -*- coding: utf-8 -*-

"""

Usage: python convert_data.py (event_name)
event_name: An optional short name, if only want to convert one event's worth of
data.
"""
import glob
import os
import sys

# 工作目录
#Since we're switching between paths, need to be relative to this.
working_dir = os.getcwd()

# 获取目标文件路径
glob_string = "data/"

if len(sys.argv) > 1:
    glob_string += sys.argv[1] + "/*/*/"
else:
    glob_string += "/*/*/*/"

dir_list = glob.glob(glob_string)

# 获取PDF文件，并对遍历进行pdftohtml -xml命令

for file_dir in dir_list:

    os.chdir(file_dir)

    file_list = glob.glob("*")

    for summary in file_list:
        command = "pdftohtml -xml " + summary
        print(command)
        os.system(command)

    # 回到工作目录
    os.chdir(working_dir)
