# -*- coding: utf-8 -*-
import asyncio
from telethon import TelegramClient
from telethon.errors.rpcerrorlist import SessionPasswordNeededError
from telethon.tl.functions.messages import GetDialogsRequest
from telethon.tl.types import InputPeerEmpty, MessageMediaDocument, DocumentAttributeAudio, MessageMediaWebPage

import csv


class MannaBotClient:
    @staticmethod
    def is_number(n):
        try:
            int(n)
        except ValueError:
            return False
        return True

    def __init__(self):
        self.api_id = 941748
        self.client_id = 821608836
        self.admin_id = 460150389
        self.api_hash = '03398ae66b58de459de3ed8a67adea40'
        self.phone = '+15014854869'
        self.client = TelegramClient(self.phone, self.api_id, self.api_hash)
        self.available_groups = {}

    async def connect(self):
        await self.client.connect()
        if not await self.client.is_user_authorized():
            await self.client.send_code_request(self.phone)
            try:
                await self.client.sign_in(self.phone, input('Enter the code: '))
            except SessionPasswordNeededError:
                await self.client.sign_in(password=input('Password: '))
        self.available_groups = await self.retrieve_group_chat_list()

    async def retrieve_group_chat_list(self):
        chats = []
        last_date = None
        chunk_size = 2000
        groups = {}
        result = await self.client(GetDialogsRequest(
            offset_date=last_date,
            offset_id=-0,
            offset_peer=InputPeerEmpty(),
            limit=chunk_size,
            hash=0
        ))
        chats.extend(result.chats)
        for chat in chats:
            try:
                groups[chat.id] = chat.title
            except Exception as e:
                print(e)
                continue
        return groups

    async def print_groups_info(self, group_name=None, save_file=True):
        chats = []
        titles = []
        last_date = None
        chunk_size = 2000
        groups = []
        result = await self.client(GetDialogsRequest(
            offset_date=last_date,
            offset_id=-0,
            offset_peer=InputPeerEmpty(),
            limit=chunk_size,
            hash=0
        ))
        chats.extend(result.chats)
        for chat in chats:
            try:
                # print(chat.title)
                # if chat.megagroup:
                groups.append(chat)
                titles.append(chat.title)
            except Exception as e:
                print(e)
                continue
        # groups = list(set(groups))
        if not group_name:
            print('Choose a group to scrape members from:')
            i = 0
            for g in groups:
                print(str(i) + '- ' + g.title + '-' + str(g.id))
                i += 1
            g_index = input("Enter a Number: ")
            target_group = groups[int(g_index)]

        else:
            try:
                g_index = titles.index(group_name)
            except Exception as e:
                print(str(e))
                target_group = None
            else:
                target_group = groups[g_index]
        if target_group:
            # print('Fetching Members...')
            all_participants = await self.client.get_participants(target_group, aggressive=True)
            all_participants_ids = {}
            all_participants_info = []
            for user in all_participants:
                if user.username:
                    username = user.username
                else:
                    username = ""
                if user.first_name:
                    first_name = user.first_name
                else:
                    first_name = ""
                if user.last_name:
                    last_name = user.last_name
                else:
                    last_name = ""
                name = (first_name + ' ' + last_name).strip()
                all_participants_ids["{}".format(name)] = user.id
                participant_info = [name, user.id, user.access_hash, username, target_group.title, target_group.id]
                all_participants_info.append(participant_info)
            if save_file:
                print('Saving In file...')
                with open("{}-members.csv".format(target_group.title.replace("/", "-")), "w",
                          encoding='UTF-8') as f:
                    writer = csv.writer(f, delimiter=",", lineterminator="\n")
                    writer.writerow(['Name', 'UserId', 'AccessHash', 'UserName', 'group', 'group id'])
                    for participant_info in all_participants_info:
                        writer.writerow(participant_info)
                print('Members scraped successfully.')
            return all_participants_ids
        else:
            raise TypeError("Please check your group name")

    async def retrieve_members_in_group(self, group):
        if self.is_number(group):
            group = await self.get_input_entity(group)
        all_participants = await self.client.get_participants(group, aggressive=True)
        all_participants_ids = []
        for user in all_participants:
            if user.id != self.client_id:
                all_participants_ids.append(user.id)
        return all_participants_ids

    async def send_message_to_user(self, user, message, reply_to=None, parse_mode='html'):
        if self.is_number(user):
            user = await self.get_input_entity(user)
        await self.client.send_message(user, message, reply_to=reply_to, parse_mode=parse_mode)

    async def send_message_to_group(self, group, message, pin=False):
        if self.is_number(group):
            group = await self.get_input_entity(group)
        message_entity = await self.client.send_message(group, message, parse_mode='html')
        if pin:
            await self.client.pin_message(group, message_entity, notify=True)

    async def delete_user_from_group(self, user_id, group_id):
        pass

    async def get_input_entity(self, entity_id):
        entity = await self.client.get_input_entity(entity_id)
        return entity

    async def clear_outdated_messages(self):
        pass


async def main():
    manna_bot = MannaBotClient()
    await manna_bot.connect()
    await manna_bot.print_groups_info()
    # dialogs = await manna_bot.client.get_dialogs(10)
    # for x in range(10):
    #     dialog = dialogs[x]
    #     print(x, dialog.title)
    # # first = dialogs[9]
    # current_date_str = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    # async for dialog in manna_bot.client.iter_dialogs():
    #     print('{:>14}: {}'.format(dialog.id, dialog.title))
    #     new_message = True
    #     async for message in manna_bot.client.iter_messages(dialog):
    #         message_created_date = message.date.astimezone(timezone('America/Los_Angeles'))
    #         message_created_date_str = message_created_date.strftime("%Y%m%d%H%M%S")
    #         try:
    #             media = message.media
    #             content = message.message
    #         except TypeError:
    #             pass
    #         except ValueError:
    #             pass
    #         else:
    #             if int(current_date_str) - int(message_created_date_str) > 24*3600*7:
    #                 print("Yes-outdate", message.sender_id)
    #                 break
    #             if message.sender_id == manna_bot.client_id:
    #                 print("ME - myself")
    #                 if "You have not posted your audio file of Romans 1:1-7" in message.message:
    #                     print("MESSSS")
    #                 break
    #             elif int(current_date_str) - int(message_created_date_str) < 1000:
    #                 print("NEW MESSAGE - NEW")
    #                 # print(message)
    #                 #break
    #             elif isinstance(media, MessageMediaDocument) and isinstance(media.document.attributes[0],
    #                                                                         DocumentAttributeAudio):
    #                 pass
    #             elif int(current_date_str) - int(message_created_date_str) > 24*3600*7:
    #                 pass
    #             else:
    #                 print("Yes", message.sender_id)

loop = asyncio.get_event_loop()
loop.run_until_complete(main())
