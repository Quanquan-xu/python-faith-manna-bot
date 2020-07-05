# -*- coding: utf-8 -*-
from telethon import TelegramClient
from telethon.errors.rpcerrorlist import SessionPasswordNeededError
from telethon.tl.functions.messages import GetDialogsRequest
from telethon.tl.types import InputPeerEmpty, MessageMediaDocument, DocumentAttributeAudio, MessageMediaWebPage, WebPage, WebPageEmpty

import csv
import datetime
from pytz import timezone
from settings import APPROVED_SCRIPTURES, CHINESE_BIBLE_REFERENCE, \
    REMIND_SCRIPTURE, REMIND_SCRIPTURE_ID, GROUPS_REPLY_MESSAGE_TITLE, MESSAGES_QUEUE, SCHEDULE_TIMES
from settings import AUDIO_MESSAGE_GUIDANCE, NON_AUDIO_MESSAGE_GUIDANCE, KEYWORDS_MESSAGE_GUIDANCE


class MannaBotClient:
    @staticmethod
    def is_number(n):
        try:
            int(n)
        except ValueError:
            return False
        except TypeError:
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


class MessageManager:
    @staticmethod
    def read_class_csv(class_name):
        current_date = datetime.datetime.now().strftime("%Y-%m-%d")
        scripture_message = {}
        with open('class/{}.csv'.format(class_name), newline='') as csv_file:
            reader = csv.DictReader(csv_file)
            for row in reader:
                if row["日期"] == current_date:
                    scripture = row["经文"]
                    content = row['内容']
                    scripture_message['scripture'] = scripture
                    scripture_message['content'] = content
                    break
        return scripture_message

    def __init__(self, target_sheet, group_id):
        self.google_sheet = target_sheet
        self.current_date = datetime.datetime.now().strftime("%Y%m%d")
        self.current_hour = int(datetime.datetime.now().strftime("%H"))
        self.current_minute = int(datetime.datetime.now().strftime("%M"))
        self.date_str = datetime.datetime.now().strftime("%A-%Y-%m-%d")
        self.status = True
        self.scripture = None
        self.scripture_content = None
        self.group_id = group_id
        self.group_name = None
        self.scripture_message_id = None
        self.scripture_reciting_rate = 6.5
        self.max_verse_title = 8
        self.min_scripture_reciting_duration = 10
        self.max_scripture_reciting_duration = 150
        self.is_first_remind_message = True
        self.first_remind_message_id = REMIND_SCRIPTURE_ID
        self.welcome_message_id = "欢迎加入"
        self.approved_message_id = '👌'
        self.excellent_message_id = '👍'
        self.approved_message = 'Please keep going with perseverance and patience in Jesus Christ!'
        self.rejected_message_id = '🙁'
        self.rejected_message = 'Please try to resend new recorded audio file !'
        self.fail_message_id = 'Next day, hope that you can continue with encouragement and confidence from God!'
        self.last_time_running = False

    def init_schedule_scripture_info(self, group_name):
        scripture_message = self.read_class_csv(self.google_sheet)
        if scripture_message:
            self.scripture = scripture_message['scripture']
            self.scripture_content = scripture_message['content']
            verses = len(self.scripture_content.split("\n"))
            scripture_length = len(self.scripture_content) - self.max_verse_title * verses
            self.min_scripture_reciting_duration = int(scripture_length / self.scripture_reciting_rate)
            self.scripture_message_id = "https://biblia.com/bible/niv/{}".format(
                self.scripture.replace(" ", "").replace(":", "."))
            self.group_name = group_name
            if self.current_hour == SCHEDULE_TIMES['deadLineHour'] and self.current_minute >= SCHEDULE_TIMES[
                'deadLineMinute']:
                self.last_time_running = True

        else:
            self.status = False

    def get_rejected_message(self):
        summary_words = '<b>    ❌ Your audio file for {} is too short to be approved ⁉️</b>'.format(self.scripture)
        encourage_words = '<i>{}</i>'.format(self.rejected_message)
        rejected_message = summary_words + "\n\n" + encourage_words
        return rejected_message

    def get_welcome_message(self):
        list_one = '<b>1、背经群介绍：</b>'
        list_two = '<b>2、发送消息形式：：</b>'
        program_info = AUDIO_MESSAGE_GUIDANCE + '\n' + NON_AUDIO_MESSAGE_GUIDANCE + '\n' + KEYWORDS_MESSAGE_GUIDANCE
        if self.current_hour < 0:
            return False
        else:
            group_info = MESSAGES_QUEUE[GROUPS_REPLY_MESSAGE_TITLE][self.group_id]
            title = group_info['title'] if group_info['title'] else self.group_name
            welcome_words = '<b>🎉🎉🎉欢迎加入' + title + '，</b>' + '<i>下面是一些说明👇:</i>'
            description_words = '<b>    描述：</b>' + '<i> {}'.format(group_info['desc']) + '</i>\n'
            duration_words = '<b>    时间：</b>' + '<i>{} 到 {}，共{}</i>\n'.format(group_info['start_date'],
                                                                              group_info['end_date'],
                                                                              group_info['duration'])
            link = '<b>    链接：</b>' + '<i>{}</i>\n\n'.format(group_info['link'])
            extra_words = '<b>{}</b>'.format(group_info['extra'])
            # text2 = '<a href="{}">'.format("#") + self.scripture + '</a>'
            group_info_message = description_words + duration_words + link + extra_words
            welcome_message = welcome_words + '\n\n' + list_one + '\n\n' + group_info_message + '\n\n\n' + list_two + '\n\n' + program_info
            return welcome_message

    def get_scripture_message(self, approved=False):
        if self.scripture and self.scripture_content:
            try:
                name = self.scripture.split(" ")[0]
                if name in list(CHINESE_BIBLE_REFERENCE.keys()):
                    language_scripture = self.scripture.replace(name, CHINESE_BIBLE_REFERENCE.get(name))
                    today_scripture = '<b>' + language_scripture + " | " + self.date_str + '</b>' + "\n\n"
                    content = '<a href="{}">'.format(
                        self.scripture_message_id) + self.scripture_content + '</a>' + "\n\n"
                    title = "<b>{}:</b>".format(self.group_name) + "\n\n"
                    reference = "<b>        我趁天未亮呼求，我仰望了你的言语； 我趁夜更未换将眼睁开，为要思想你的话语</b>"
                    if approved:
                        title = ""
                    scripture_message = title + today_scripture + content + reference
                    return scripture_message
                else:
                    print("Scripture name has something wrong, which should be English!")
                    return False
            except Exception as e:
                print(e)
        else:
            return False

    def get_remind_message(self):
        if self.current_hour < SCHEDULE_TIMES["minHourOfSendingRemindMessage"]:
            return False
        else:
            left_hour = 24 - self.current_hour
            if self.current_minute < SCHEDULE_TIMES["maxMinuteInHourOfSendingRemindMessage"] or self.is_first_remind_message:
                text1 = '<b>   You have not posted your audio file of </b>'
                text2 = '<b>' + self.scripture + '</b>'
                text3 = '<b> to me</b>'
                text4 = '<i>' + 'There is only less than {} hours left... \nPlease save your time !'.format(
                    left_hour) + '</i>'

                if self.is_first_remind_message:
                    remind_message = text1 + text2 + text3 + "\n\n" + text4 + "\n\n" + REMIND_SCRIPTURE
                else:
                    remind_message = '<i>' + 'There is only less than ' + '</i>' + '<b>' + '{} hours left '.format(
                        left_hour) + '</b>' + \
                                     '<i>' + '... \nPlease save your time !' + '</i>'
                return remind_message
            else:
                if self.last_time_running:
                    date_str = '<i>' + datetime.datetime.now().strftime("%d %b %Y %H:%M:%S") + '</i>'
                    text1 = '<i>⁉️️Sorry to inform :</i>'
                    text2 = '<i>You have lost the last chance for automatic program to check your audio file of </i>'
                    text3 = '<b>' + self.scripture + '</b>'
                    text4 = '<i>{}</i>'.format(self.fail_message_id)
                    remind_message = text1 + "\n\n" + text2 + text3 + "\n\n" + text4 + "\n\n" + '<b>' + date_str + '</b>'
                    return remind_message
                else:
                    return False

    def get_approved_message(self, code):
        summary_words = '<b>    💯 Your audio file for {} has been approved!!</b>'.format(self.scripture)
        encourage_words = '<i>  {}</i>'.format(self.approved_message)

        if code < 200:
            index = 1
        elif 200 <= code < 530:
            index = 2
        elif 530 <= code < 700:
            index = 3
        elif 700 <= code < 1200:
            index = 4
        elif 1200 <= code < 1330:
            index = 5
        elif 1330 <= code < 1700:
            index = 6
        elif 1700 <= code < 2000:
            index = 7
        elif 2000 <= code < 2130:
            index = 8
        elif 2130 <= code < 2330:
            index = 9
        elif 2330 <= code < 2359:
            index = 10
        else:
            index = 8
        approved_scripture = APPROVED_SCRIPTURES[index - 1]
        text5 = '<b><i>' + approved_scripture + '</b></i>'
        approved_message = summary_words + "\n\n" + encourage_words + "\n\n" + text5
        return approved_message


class ScriptureScheduler:
    def __init__(self, target_sheet, group_id, group_name=None):
        self.manna_bot = MannaBotClient()
        self.client_bot = None
        self.message_manager = MessageManager(target_sheet, group_id)
        self.group_id = group_id
        self.group_name = group_name
        self.group_member_ids = None

    async def connect(self):
        await self.manna_bot.connect()
        self.client_bot = await self.manna_bot.get_input_entity(self.manna_bot.client_id)
        if not self.group_name:
            self.group_name = self.manna_bot.available_groups[self.group_id]
        self.group_member_ids = await self.manna_bot.retrieve_members_in_group(self.group_id)
        self.message_manager.init_schedule_scripture_info(self.group_name)

    async def clear_redundant_messages(self, entity, keywords="hours left"):
        approved_audio_ids = []
        async for message in self.manna_bot.client.iter_messages(entity, limit=30):
            try:
                media = message.media
                message_created_date = message.date.astimezone(timezone('America/Los_Angeles'))
                message_created_date_str = message_created_date.strftime("%Y%m%d")
                if message_created_date_str == self.message_manager.current_date:
                    if keywords in message.message:
                        await message.delete()
                    elif isinstance(media, MessageMediaDocument) and isinstance(media.document.attributes[0],
                                                                                DocumentAttributeAudio):
                        audio_created_date = message.media.document.date.astimezone(timezone('America/Los_Angeles'))
                        audio_created_date_str = audio_created_date.strftime("%Y%m%d")
                        duration = media.document.attributes[0].duration
                        if audio_created_date_str == self.message_manager.current_date and duration:
                            if message.id not in approved_audio_ids:
                                await message.delete()
                    elif isinstance(message.media, MessageMediaWebPage):
                        if isinstance(message.media.webpage, WebPage):
                            if message.media.webpage.url != self.message_manager.scripture_message_id:
                                await message.delete()
                        elif isinstance(message.media.webpage, WebPageEmpty):
                            pass
                        else:
                            await message.delete()
                    else:
                        if message.message == self.message_manager.approved_message_id:
                            approved_audio_ids.append(message.reply_to_msg_id)
                        elif message.message == self.message_manager.excellent_message_id:
                            approved_audio_ids.append(message.reply_to_msg_id)
                        elif self.message_manager.approved_message in message.message:
                            pass
                        else:
                            await message.delete()
            except TypeError:
                pass
            except ValueError:
                pass
            except TabError:
                pass

    async def delete_remind_messages(self, entity, keywords="hours left"):
        async for message in self.manna_bot.client.iter_messages(entity, limit=10, from_user=self.client_bot):
            text = message.message
            if text and keywords in text:
                created_date = message.date.astimezone(timezone('America/Los_Angeles')).strftime(
                    "%Y%m%d")
                if created_date == self.message_manager.current_date:
                    await message.delete()

    async def evaluate_audio_durations(self, audio_ids, audio_durations, member):
        min_duration = self.message_manager.min_scripture_reciting_duration
        if len(audio_ids) == 1:
            audio_id = audio_ids[0]
            if audio_durations[audio_id] - min_duration < 0:
                await self.manna_bot.send_message_to_user(member, self.message_manager.rejected_message_id,
                                                                  audio_id)
                rejected_message = self.message_manager.get_rejected_message()
                await self.manna_bot.send_message_to_user(member, rejected_message)
                return False
            return audio_id
        else:
            durations = [audio_durations[audio_id] for audio_id in audio_ids]
            evaluated_durations = [duration-min_duration for duration in durations]
            best_audio_id = None
            better_audio_id = None
            for evaluated_duration in evaluated_durations:
                if evaluated_duration > 0 and evaluated_duration - int(min_duration / 4) <= 0:
                    best_audio_id = audio_ids[evaluated_durations.index(evaluated_duration)]
                    break
            if best_audio_id:
                return best_audio_id
            else:
                for evaluated_duration in evaluated_durations:
                    if evaluated_duration > 0:
                        better_audio_id = audio_ids[evaluated_durations.index(evaluated_duration)]
                        break
                if better_audio_id:
                    return better_audio_id
                else:
                    rejected_message = self.message_manager.get_rejected_message()
                    for audio_id in audio_ids:
                        await self.manna_bot.send_message_to_user(member, self.message_manager.rejected_message_id,
                                                                  audio_id)
                        await self.manna_bot.send_message_to_user(member, rejected_message)
                    return False

    async def check_scripture_message(self, to_user, from_user):
        index = 0
        async for message in self.manna_bot.client.iter_messages(to_user, limit=10, from_user=from_user):
            index += 1
            message_created_date = message.date.astimezone(timezone('America/Los_Angeles'))
            message_created_date_str = message_created_date.strftime("%Y%m%d")
            if message_created_date_str == self.message_manager.current_date:
                if isinstance(message.media, MessageMediaWebPage):
                    if isinstance(message.media.webpage, WebPage):
                        if message.media.webpage.url == self.message_manager.scripture_message_id:
                            return True, index
        return False, index

    async def get_progress_message_code(self, to_user):
        audio_message_ids = {}
        audio_duration_ids = {}
        approved_audio_message_ids = {}
        rejected_audio_ids = []
        index = 0
        async for message in self.manna_bot.client.iter_messages(to_user, limit=30):
            index += 1
            try:
                media = message.media
                content = message.message
            except TypeError:
                pass
            except ValueError:
                pass
            else:
                message_created_date = message.date.astimezone(timezone('America/Los_Angeles'))
                message_created_date_str = message_created_date.strftime("%Y%m%d")
                if message_created_date_str == self.message_manager.current_date:
                    if isinstance(media, MessageMediaDocument) and isinstance(media.document.attributes[0],
                                                                              DocumentAttributeAudio):
                        audio_created_date = message.media.document.date.astimezone(timezone('America/Los_Angeles'))
                        audio_created_date_str = audio_created_date.strftime("%Y%m%d")
                        duration = media.document.attributes[0].duration
                        if audio_created_date_str == self.message_manager.current_date and duration:
                            if message.id not in rejected_audio_ids:
                                approved_code = int(audio_created_date.strftime("%H%M"))
                                audio_message_ids[message.id] = approved_code
                                audio_duration_ids[message.id] = duration
                            else:
                                await message.delete()
                    elif isinstance(message.media, MessageMediaWebPage):
                        if isinstance(message.media.webpage, WebPage):
                            if message.media.webpage.url == self.message_manager.scripture_message_id:
                                print("Yes")
                                if self.message_manager.group_name in message.message:
                                    available_audio_ids = list(
                                        audio_message_ids.keys() - approved_audio_message_ids.keys())
                                    audio_message = None
                                    if available_audio_ids:
                                        audio_id = await self.evaluate_audio_durations(available_audio_ids,
                                                                                       audio_duration_ids, to_user)
                                        if audio_id:
                                            audio_message = {
                                                "audio_id": audio_id,
                                                "approved_code": audio_message_ids[audio_id],
                                                "duration": audio_duration_ids[audio_id]
                                            }
                                        else:
                                            audio_message = False
                                    return message.id, audio_message
                                else:
                                    return 1, message.id
                    else:
                        if content == self.message_manager.approved_message_id or content == self.message_manager.excellent_message_id:
                            approved_code = int(message_created_date.strftime("%H%M"))
                            approved_audio_message_ids[message.reply_to_msg_id] = approved_code
                        elif content == self.message_manager.rejected_message_id:
                            rejected_audio_ids.append(message.reply_to_msg_id)
                            await message.delete()
                        else:
                            if self.message_manager.first_remind_message_id in content:
                                self.message_manager.is_first_remind_message = False
                            if self.message_manager.rejected_message in content:
                                await message.delete()
        if index:
            return 0, None
        else:
            return -1, None

    async def broadcast_scripture_message(self):
        scripture_message = self.message_manager.get_scripture_message()
        for member_id in self.group_member_ids:
            try:
                member = await self.manna_bot.get_input_entity(member_id)
                scripture_message_status, index = await self.check_scripture_message(member, self.client_bot)
                print(scripture_message_status)
                print(index)
                if not scripture_message_status:
                    if not index:
                        welcome_message = self.message_manager.get_welcome_message()
                        if welcome_message:
                            await self.manna_bot.send_message_to_user(member, welcome_message)
                    if scripture_message:
                        await self.manna_bot.send_message_to_user(member, scripture_message)
                else:
                    await self.broadcast_progress_message()
            except Exception as e:
                print(str(e))

    async def broadcast_progress_message(self):
        if self.message_manager.scripture_content:
            for member_id in self.group_member_ids:
                try:
                    member = await self.manna_bot.get_input_entity(member_id)
                    message_code, audio_message = await self.get_progress_message_code(member)
                    print(message_code)
                    print(audio_message)
                    if message_code > 1:
                        if audio_message:
                            audio_id = audio_message['audio_id']
                            approved_code = audio_message['approved_code']
                            duration = audio_message["duration"]
                            if duration >= self.message_manager.max_scripture_reciting_duration:
                                await self.manna_bot.send_message_to_user(member,
                                                                          self.message_manager.excellent_message_id,
                                                                          audio_id)
                            else:
                                await self.manna_bot.send_message_to_user(member,
                                                                          self.message_manager.approved_message_id,
                                                                          audio_id)
                            approved_message = self.message_manager.get_approved_message(approved_code)
                            await self.manna_bot.send_message_to_user(member, approved_message, message_code)
                            approved_scripture_message = self.message_manager.get_scripture_message(True)
                            await self.manna_bot.client.edit_message(member, message_code, approved_scripture_message,
                                                                     parse_mode='html')
                            await self.delete_remind_messages(member)
                        else:
                            if not isinstance(audio_message, bool):
                                remind_message = self.message_manager.get_remind_message()
                                if remind_message:
                                    reply_to = None
                                    if self.message_manager.first_remind_message_id in remind_message or self.message_manager.fail_message_id in remind_message:
                                        reply_to = message_code
                                    await self.manna_bot.send_message_to_user(member, remind_message, reply_to)
                                    if self.message_manager.fail_message_id in remind_message:
                                        approved_scripture_message = self.message_manager.get_scripture_message(True)
                                        await self.manna_bot.client.edit_message(member, message_code,
                                                                                 approved_scripture_message,
                                                                                 parse_mode='html')
                                        await self.delete_remind_messages(member)
                    elif message_code < 0:
                        welcome_message = self.message_manager.get_welcome_message()
                        if welcome_message:
                            await self.manna_bot.send_message_to_user(member, welcome_message)
                    else:
                        if self.message_manager.last_time_running:
                            await self.clear_redundant_messages(member)
                except Exception as e:
                    print(str(e))

    async def run(self):
        await self.connect()
        if self.message_manager.status:
            if self.message_manager.current_hour <= SCHEDULE_TIMES['maxHourOfSendingScriptureMessage']:
                await self.broadcast_scripture_message()
            else:
                await self.broadcast_progress_message()
