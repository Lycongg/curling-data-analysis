1.环境：运行setup.sh
2.find_and_download_input_files.py 生成data目录并爬取世界冰壶联合会官网的shot-by-shot，PDF文件
3.convert_data.py 在pdf目录下将PDF文件转换成xml和png图片
4.creat_database.py 创建数据库，数据表
5.populate.py 解析xml和png图片并把数据写入数据库
# curling-data-analysis
