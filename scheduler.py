# -*- coding: utf-8 -*-
import argparse
import asyncio
from telegram.client import ScriptureScheduler


async def schedule_scripture(target_sheet, group_id, group_name=None):
    scripture_scheduler = ScriptureScheduler(target_sheet, group_id, group_name)
    await scripture_scheduler.connect()
    await scripture_scheduler.run()

parser = argparse.ArgumentParser(description='manual to scripture schedule')
parser.add_argument('--sheet-name', type=str, default="")
parser.add_argument('--group-id', type=int, default=0)
parser.add_argument('--group-name', type=str, default=None)
args = parser.parse_args()
google_sheet = args.sheet_name
chat_id = args.group_id
chat_name = args.group_name
if google_sheet and chat_id:
    loop = asyncio.get_event_loop()
    loop.run_until_complete(schedule_scripture(google_sheet, chat_id, chat_name))
else:
    print("There is something wrong with sheet name or group id !")

# python scheduler.py --sheet-name=Romans-v1 --group-id=498694591