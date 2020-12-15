
# -*- coding: utf-8 -*-


"""
此脚本遍历XML和.png文件（data/<EVENT_NAME>）运行完此脚本后，数据库中会填充所有数据目录的内容。

为了便于添加新比赛事件（并用于测试），可以通过在命令行上指定比赛名称使用一个比赛事件模式。

用法：python populate_db.py（short_name）
     short_name是可选参数，仅添加一个比赛。
"""

import database_functions as db
from datetime import datetime
import pdf_parsing_functions as pf
import glob
import sys
import os
import xml.etree.ElementTree as ET


# 获取当前工作目录
working_directory = os.getcwd()

# data目录为起始目录
starting_directory = "data/"

# 转到起始目录
os.chdir(starting_directory)

# 如果在命令行上提供了赛事名称，则将其放在列表中。否则，使用glob获取比赛列表，并进行排序。
short_names = []

if len(sys.argv) > 1:
    short_names.append(sys.argv[1])

else:
    short_names = glob.glob("*")
    short_names = sorted(short_names)


# 通过目录树来构建数据库
for event in short_names:

    # 数据库表为每个赛事设置的变量
    # id：此赛事的ID号，主键。
    # name_short：此赛事的名称的缩写。
    # start_date：此赛事的开始日期。
    # end_date：此赛事的结束日期。
    # 赛事的开始和结束日期通过PDF文件获取，之后读PDF时再更新
    event_id = db.get_next_id("events")
    event_name = event
    event_start_date = ""
    event_start_datetime = datetime.max  # 占位
    event_end_date = ""
    event_end_datetime = datetime.min  # 占位

    c = """
        INSERT INTO events (
            id, 
            name)
            VALUES (
            "{}",
            "{}");
            """
    db.run_command(c.format(event_id, event_name))


    # 转到下一目录：比赛类型
    # 遍历文件并排序
    os.chdir(event)
    game_types = glob.glob("*")
    game_types = sorted(game_types)
    for gt in game_types:

        # 转到下一级目录
        os.chdir(gt)

        # 转换名称，方便存于数据库
        game_type = ""
        if gt == "Men\'s_Teams":
            game_type = "Men"
        elif gt == "Women\'s_Teams":
            game_type = "Women"
        else:
            game_type = "Unknown"


        # 其余的信息可以从PDF文件中获取，接下来继续遍历
        session_names = glob.glob("*")
        session_names = sorted(session_names)
        for session in session_names:
            
            # 遍历场次，并获取xml文件
            os.chdir(session)
            xml_files = glob.glob("*.xml")
            xml_files = sorted(xml_files)

            # 终端提示正在处理的文件，然并卵
            print("Processing: " + event + " " + session)

            # 遍历xml文件，获取所需信息
            for gf in xml_files:

                # 在数据库中game表中加入以下键
                game_id = db.get_next_id("games")
                
                # 获取game_session，修改文件名即可
                game_session = session[session.rindex("~") + 1:]
                
                #以下键的值来自PDF文件，先存空
                game_red = ""
                game_yellow = ""
                game_red_score = 0
                game_yellow_score = 0
                name_and_sheet = {}
                date_and_time = {}
                first_shot_color = ""
                team_to_color = {}
                color_to_team = {}


                #遍历xml，每一页都对应一回合
                tree = ET.parse(gf)
                pages = tree.getroot()
                for ip in range(len(pages)):

                    # 如果是第一页，获取比赛基本信息
                    # 获取每一页PDF的图片
                    image_list = pf.get_image_list(pages[ip])
                    if ip == 0:
                        name_and_sheet = pf.get_name_and_sheet(pages[ip])
                        date_and_time = pf.get_date_and_time(pages[ip])

                        # game表的信息基本获取结束
                        # 到此,event表信息还不完整 
                        # 建立回合，shots，冰壶位置表

                        c = """
                        INSERT INTO games (
                        id,
                        event_id,
                        session,
                        name,
                        sheet,
                        type,
                        start_date,
                        start_time)
                        VALUES (
                        "{}",
                        "{}",
                        "{}",
                        "{}",
                        "{}",
                        "{}",
                        "{}",
                        "{}");
                        """
                        db.run_command(c.format(game_id, event_id, session,
                            name_and_sheet["name"], name_and_sheet["sheet"],
                            game_type, date_and_time["date"],
                            date_and_time["time"]))

                        # 对比获取时间
                        #bounds of the event for writing to the event table. 
                        curr_datetime = datetime.strptime(date_and_time["date"], "%a %d %b %Y")

                        if(curr_datetime < event_start_datetime):
                            event_start_datetime = curr_datetime
                            event_start_date = date_and_time["date"]

                        if(curr_datetime > event_end_datetime):
                            event_end_datetime = curr_datetime
                            event_end_date = date_and_time["date"]

                    # 建立end(回合)表
                    end_id = db.get_next_id("ends")
                    
                    # end number是页码数 (索引加1)
                    end_number = ip + 1

                    # 更新end表
                    c = """
                    INSERT INTO ends(
                    id,
                    game_id,
                    number)
                    VALUES(
                    "{}",
                    "{}",
                    "{}");
                    """
                    db.run_command(c.format(end_id, game_id, end_number))

                    # 遍历图片
                    #Store the previous maximum element index in the loop
                    #through the elements in the page for each shot, so that we
                    #don't have to waste time looping over elements we've
                    #already considered.
                    prev_max_elt_index = 0
                    
                    # 获取颜色和投掷方向
                    color_hammer = ""
                    direction_of_play = ""
                    for si in range(len(image_list)):
                        
                        shot_id = db.get_next_id("shots")

                        # 投掷号
                        shot_number = si + 1

                        #调用函数获取冰壶位置，返回dataframe
                        #This function takes the path to the image, which is in
                        #the "src" attribute of this element.
                        stone_df = pf.get_rock_positions(image_list[si].attrib["src"])

                        # 如果是第一次投掷，获取投掷方向和冰壶颜色
                        if si == 0:
                            direction_of_play = pf.get_direction_of_play(stone_df)
                            first_shot_color = pf.get_1st_shot_color(stone_df)

                            # 获取队伍颜色
                            if first_shot_color == "red":
                                color_hammer = "yellow"
                            elif first_shot_color == "yellow":
                                color_hammer = "red"
                            else:
                                color_hammer = "error_color"

                            bool_dir_of_play = 0
                            if direction_of_play == "up":
                                bool_dir_of_play = 1

                            # 更新冰壶颜色和投掷方向
                            c = """
                            UPDATE ends
                            SET direction = "{}", color_hammer = "{}"
                            WHERE id = "{}";
                            """
                            db.run_command(c.format(bool_dir_of_play, color_hammer, end_id))
                            
                        

                        
                        #Now that we have the direction of play and the color
                        #of the first shot, standardize to one coordinate
                        #system and clean out all but the stones in play.
                        stone_positions = pf.clean_rock_positions(stone_df,
                            direction_of_play)

                        #Now, get the data for this shot.
                        shot_data = pf.get_shot_data(pages[ip], si + 1,
                            image_list, prev_max_elt_index)

                        #If this is the first shot of the first end, use this
                        #information to map team to shot color.
                        if (si == 0) and (ip == 0):
                            team_to_color[shot_data["team"]] = first_shot_color
                            

                        #If it's the second shot of the first end, fill in the
                        #other team's name and shot color (i.e. color_hammer)
                        elif (si == 1) and (ip == 0):
                            team_to_color[shot_data["team"]] = color_hammer

                            #Now fill the color_to_team variable, for easy
                            #conversion the other way.
                            for elt in team_to_color.items():
                                color_to_team[elt[1]] = elt[0]


                            # 更新数据库
                            c = """
                            UPDATE games
                            SET team_red = "{}", team_yellow = "{}"
                            WHERE id = "{}";
                            """
                            db.run_command(c.format(color_to_team["red"],
                                color_to_team["yellow"], game_id))



                        #Extract the maximum element index for use in the next
                        #shot.
                        prev_max_elt_index = shot_data["max_elt_index"]

                        #At this point we should have all the shot data we need
                        #to assemble a full record. Do so now.
                        c = """
                        INSERT INTO shots (
                        id,
                        end_id,
                        number,
                        color,
                        team,
                        player_name,
                        type,
                        turn,
                        percent_score)
                        VALUES (
                        "{}",
                        "{}",
                        "{}",
                        "{}",
                        "{}",
                        "{}",
                        "{}",
                        "{}",
                        "{}");
                        """
                        db.run_command(c.format(shot_id,
                            end_id, 
                            shot_number,
                            team_to_color[shot_data["team"]],
                            shot_data["team"],
                            shot_data["player_name"],
                            shot_data["type"],
                            shot_data["turn"],
                            shot_data["percent_score"]))

                        #Now that there is an entry for the shot data, we can
                        #write out the stone positions for this shot.
                        #stone_positions already contains all the data for this
                        #shot, so we just need to iterate over it and write
                        #each row to the database.
                        for sp_index, sp_row in stone_positions.iterrows():
                            stone_id = db.get_next_id("stone_positions")

                            c = """
                            INSERT INTO stone_positions(
                            id,
                            shot_id,
                            color,
                            x,
                            y)
                            VALUES (
                            "{}",
                            "{}",
                            "{}",
                            "{}",
                            "{}");
                            """
                            db.run_command(c.format(stone_id,
                                shot_id,
                                sp_row["color"],
                                sp_row["x"],
                                sp_row["y"]))
                        

                    #On every page we need to extract the score and the time
                    #left.
                    score_and_time = pf.get_score_and_time(pages[ip], 
                        prev_max_elt_index)


                    #Only deal with the score and time remaining if the box is
                    #present (the score_and_time variable is not None.
                    if(score_and_time is not None):
                   
                        #Fill score and time remaining for the end.
                        c = """
                        UPDATE ends
                        SET score_red = "{}", score_yellow = "{}",
                        time_left_red = "{}", time_left_yellow = "{}"
                        WHERE id = "{}"
                        """
                        db.run_command(c.format(score_and_time["score"][color_to_team["red"]],
                            score_and_time["score"][color_to_team["yellow"]],
                            score_and_time["time_left"][color_to_team["red"]],
                            score_and_time["time_left"][color_to_team["yellow"]],
                            end_id))


                        #If it's the last page, fill the final score variable
                        #and write it to the database.
                        if ip == len(pages) - 1:
                            game_red_score = score_and_time["score"][color_to_team["red"]]
                            game_yellow_score = score_and_time["score"][color_to_team["yellow"]]
                            c = """
                            UPDATE games
                            SET final_score_red = "{}", final_score_yellow = "{}"
                            WHERE id = "{}";
                            """
                            db.run_command(c.format(game_red_score,
                                game_yellow_score, game_id))



               


            #Now that we're done with the session, go up one level so we can
            #continue to the next session.
            os.chdir("..")

        #Now that we've gone through all the session, go up one level to the
        #game types directory.
        os.chdir("..")


    #Now that we've gone through all the game types, go up one level so we can
    #pull the next event.
    os.chdir("..")

    #Update the event entry with the start and end dates before proceeding to
    #the next event.
    c = """
    UPDATE events
    SET start_date = "{}", end_date = "{}"
    WHERE id = "{}";
    """
    db.run_command(c.format(event_start_date, event_end_date, event_id))

