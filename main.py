from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes, CallbackContext
import asyncio
from urllib.parse import urlparse
import time
from datetime import datetime, timedelta
import random
import string
import httpx
from collections import defaultdict
import json
import os
import sys
admin_ids = [8070038689, 6994252892]  
PRIVATE_DSTAT_USER_ID = [5145402317, 6947357753, 6994252892]
BOT_TOKEN = "7537640522:AAE3393wr_uQ8Fje1Dk8DD09nOHPPu9V_Ck"

group_id = -1002674264874
GROUP_ID = -1002533465722

from functions import add_user_to_subscribed, save_running_server, remove_running_server, save_log, load_user_language, save_user_language, load_running_server, load_servers, load_l4servers, load_filtered_servers, summary_and_cleanup, load_data, save_data, summary_and_cleanup_l4,load_user_ids,save_user_ids,load_servers_clf,format_number,count_server_usage,load_vip_users,load_blocked_users,save_blocked_user,format_percentage,translate_source,translate_action

from trigger import get_description

from ranking import show_servers, show_servers_l4, protection_buttons, protection_buttons_for_top, show_top_for_server, show_top_servers_l4, show_top_servers_l7, show_top_for_server_l4

from daily_top import daily_top_servers_l7,protection_buttons_daily_top,daily_top_servers_l4,show_daily_top_for_server,show_daily_top_for_server_l4

from admin_commands import add_server, add_server_l4, remove_server, remove_server_l4, list_servers, clr, delete_ranking, delete_ranking_l4, reset_rank, ban, load_banned_users, unban, lock_group, is_group_locked, unlock_group, fake_l7, fake_l4, maintenance_mode, is_maintenance_mode

from status import show_server_status

from fetching import fetch_nginx_status, fetch_netdata, fetch_clfdata, fetch_passdata, fetch_captcha, fetch_passip, fetch_statistics, fetch_statistics_pass

from cloudflare_dstat import show_servers_clf


from captcha import captcha_count_ip_buttons

from aurologic import handle_stats_aurologic

from license import license_command,key_command,has_valid_license

from graph import send_pre_graph_to_user
from save_user_data import save_user_performance, save_user_performance_daily
from custom import handle_topshield_stats

async def get_country_name(country_code):
    api_url = f"https://restcountries.com/v3.1/alpha/{country_code}"
    async with httpx.AsyncClient() as client:
        response = await client.get(api_url)
        if response.status_code == 200:
            country_data = response.json()
            return country_data[0]['name']['common']
        return None


def generate_random_query(length=6):
    return ''.join(random.sample(string.ascii_lowercase, length))

async def is_user_in_group(user_id: int, group_id: int, context: ContextTypes.DEFAULT_TYPE) -> bool:
    try:
        member = await context.bot.get_chat_member(chat_id=group_id, user_id=user_id)
        return member.status in ['member', 'administrator', 'creator']
    except:
        return False

user_start_count = defaultdict(list)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
  user_id = str(update.effective_user.id)
  user_ids = load_user_ids()
  user_name = update.effective_user.username
  banned_users = load_banned_users()
  blocked_users = load_blocked_users()
  full_name = update.effective_user.full_name

  if user_id in blocked_users:
      return
  if user_id in banned_users:
      return

  current_time = datetime.utcnow()
  user_start_count[user_id] = [t for t in user_start_count[user_id] if current_time - t < timedelta(seconds=1)]
  
  if not await is_user_in_group(user_id, GROUP_ID, context):
      button = InlineKeyboardButton("JOIN NOW 🔰", url="https://t.me/+DXpXojJq37E1MzQ1")
      keyboard = InlineKeyboardMarkup([[button]])
      message = (
          "<blockquote><b>🇻🇳Vie\n"
          "🔍 Bạn đang tìm kiếm một công cụ hiện đại và hoàn toàn miễn phí để phân tích khả năng DDoS của mình? Hãy tham gia nhóm của chúng tôi ngay! Với dịch vụ của AIKO LOGS, bạn sẽ được trải nghiệm khả năng giám sát hệ thống vượt trội, với nhiều server hỗ trợ và kết quả cực kỳ trực quan, đa dạng về biểu đồ và thể loại phân tích. Hãy tham gia nhóm của chúng tôi để được sử dụng dịch vụ hoàn toàn MIỄN PHÍ! 🚀</b></blockquote>\n\n"
          "<blockquote><b>🇬🇧Eng\n"
          "🔍 Are you looking for a modern and completely free tool to analyze your DDoS capabilities? Join our group now! With AIKO LOGS service, you’ll experience superior system monitoring, with multiple servers supported and highly visual, diverse graphs and dstat types. Join our group to use the service completely FREE! 🚀</b></blockquote>"
      )
      await context.bot.send_message(
          chat_id=update.effective_chat.id, 
          text=message, 
          reply_markup=keyboard,
          parse_mode='HTML'
      )
      return

  if user_id not in user_ids:
      user_ids.append(user_id)
      save_user_ids(user_ids)
  await show_start_menu(update, context)


async def send_notification(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:

    if update.effective_user.id not in admin_ids:
        return
    message = '<b>-----MESSAGE FROM ADMIN-----</b>\n\n' + ' '.join(context.args)
    if not message:
        await update.message.reply_text("Nhập tin nhắn cần thông báo !")
        return

    user_ids = load_user_ids()
    successful_sends = 0
    for user_id in user_ids:
        try:
            await context.bot.send_message(chat_id=user_id, text=message,parse_mode="HTML")
            successful_sends += 1
        except Exception as e:
            print(f"Error sending message to {user_id}: {e}")
    total_users = len(user_ids)
    await update.message.reply_text(f"Gửi thông báo thành công tới <b>{successful_sends}/{total_users}</b> người dùng",parse_mode="HTML")

async def show_start_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.effective_user.full_name
    user_id = update.effective_user.id
    language = load_user_language(user_id)
    banned_users = load_banned_users()
    chat_id = update.effective_chat.id
    
    if user_id in banned_users:
        return

    if is_group_locked(chat_id) and update.effective_user.id not in admin_ids:
        return

    if is_maintenance_mode() and update.effective_user.id not in admin_ids:
        await update.message.reply_text("⚠️ Bot Maintenance ⚠️")
        return

    if language == 'vi':
        welcome_message = "👋 Chào mừng bạn đến với AIKO 2.0 – Bot hoàn toàn <b>MIỄN PHÍ</b>, mọi góp ý vui lòng liên hệ Quản trị viên 👾"

        buttons = [
            [
                InlineKeyboardButton("Layer 4 Dstat", callback_data='layer4_dstat'),
                InlineKeyboardButton("Layer 7 Dstat", callback_data='layer7_dstat')
            ],
            [
                InlineKeyboardButton("Dstat Từ Dữ Liệu Cloudflare", callback_data='cloudflare_dstat'),
            ],
            [
                InlineKeyboardButton("Bảng xếp hạng", callback_data='leaderboard')
            ],
            [
                InlineKeyboardButton("Cài đặt", callback_data='setting'),
                InlineKeyboardButton("Liên hệ Admin", url="https://t.me/KeAiAiko")
            ]
        ]
        if user_id in PRIVATE_DSTAT_USER_ID:
            buttons.append([InlineKeyboardButton("Nation + Count IP", callback_data='private_captcha_count_ip')])
    else:
        welcome_message = "👋 Welcome to AIKO 2.0 – Use the bot for <b>FREE</b>! Questions or feedback? Contact an Administrator 👾"

        buttons = [
            [
                InlineKeyboardButton("Layer 4 Dstat", callback_data='layer4_dstat'),
                InlineKeyboardButton("Layer 7 Dstat", callback_data='layer7_dstat')
            ],
            [
                InlineKeyboardButton("Cloudflare Statistics Dstat", callback_data='cloudflare_dstat'),
            ],
            [
                InlineKeyboardButton("Leaderboard", callback_data='leaderboard')
            ],
            [
                InlineKeyboardButton("Setting", callback_data='setting'),
                InlineKeyboardButton("Contact Admin", url="https://t.me/KeAiAiko")
            ]
        ]
        if user_id in PRIVATE_DSTAT_USER_ID:
            buttons.append([InlineKeyboardButton("Nation + Count IP", callback_data='private_captcha_count_ip')])
    buttons.append([InlineKeyboardButton("View My Plan", callback_data='see_my_plan')])

    reply_markup = InlineKeyboardMarkup(buttons)

    await context.bot.send_message(chat_id=update.effective_chat.id, text=welcome_message, reply_markup=reply_markup, parse_mode="HTML")



async def show_settings(update: Update, context: CallbackContext) -> None:
    language = load_user_language(update.effective_user.id) 
    message_text = "🃏 <b>Choose Your Language</b>\n" + "➖" * 12 

    buttons = [
        [
            InlineKeyboardButton("Vietnamese", callback_data='lang_vi'),
            InlineKeyboardButton("English", callback_data='lang_en')
        ]
    ]

    reply_markup = InlineKeyboardMarkup(buttons)

    if update.callback_query:
        await update.callback_query.edit_message_text(message_text, reply_markup=reply_markup)
    else:
        await update.message.reply_text(message_text, reply_markup=reply_markup,parse_mode="HTML")

def format_number(number):
    return f"{number:,}"

#######  FETCHING DATA FUNCTION  #######
async def handle_stats(update: Update, context: ContextTypes.DEFAULT_TYPE, server_info, time):
  chat_id = update.effective_chat.id
  user_name = update.callback_query.from_user.username
  language = load_user_language(update.effective_user.id)
  user_id = update.effective_user.id

  await context.bot.send_message(chat_id=chat_id, text=f"🎬 <b>Bắt Đầu Ghi Nhận Request Của {server_info['name']} bởi @{user_name}</b>" if language == "vi" else f"🎬 <b>Start Recording Request For {server_info['name']} by @{user_name}</b>",parse_mode="HTML")
  for _ in range(server_info['time']):
      await update_user_data(update, context, server_info['url'])
      await asyncio.sleep(0.6)
  remove_running_server(user_id)
  await summary_and_cleanup(update, context, server_info['name'])


async def handle_stats_captcha(update: Update, context: ContextTypes.DEFAULT_TYPE, path):
    chat_id = update.effective_chat.id
    user_name = update.callback_query.from_user.username
    language = load_user_language(update.effective_user.id)
    user_id = update.effective_user.id
    full_name = update.callback_query.from_user.full_name

    try:
        message = await context.bot.send_message(
            chat_id=chat_id,
            text=f"🎬 <b>Bắt Đầu Ghi Nhận Tấn Công Của Captcha Count IP bởi @{user_name}</b>" if language == "vi" else f"🎬 <b>Start Recording Attack For 200s by @{user_name}</b>",
            parse_mode="HTML"
        )

        start_time = datetime.utcnow()
        duration = 200
        remaining_time = duration

        while remaining_time > 0:
            current_time = datetime.utcnow()
            events = await fetch_captcha(update, user_id, start_time, current_time, path)
            events2, _ = await fetch_passip(update, user_id, start_time, current_time, path)

            successful_requests = [event for event in events2]
            blocked_requests = [event for event in events if event['dimensions']['originResponseStatus'] == 0]

            def summarize(events):
                total_requests = sum(event['count'] for event in events)
                unique_ips = set(event['dimensions']['clientIP'] for event in events)
                total_ips = len(unique_ips)

                country_ip_counts = {}
                asn_counts = {}

                for event in events:
                    country = event['dimensions']['clientCountryName']
                    asn = event['dimensions']['clientASNDescription']

                    if country not in country_ip_counts:
                        country_ip_counts[country] = set()
                    country_ip_counts[country].add(event['dimensions']['clientIP'])

                    asn_counts[asn] = asn_counts.get(asn, 0) + event['count']

                sorted_country_ip_counts = sorted(country_ip_counts.items(), key=lambda x: len(x[1]), reverse=True)[:10]
                sorted_asn_counts = sorted(asn_counts.items(), key=lambda x: x[1], reverse=True)[:10]

                total_nations = len(country_ip_counts)

                return total_requests, total_ips, sorted_country_ip_counts, sorted_asn_counts, total_nations

            success_stats = summarize(successful_requests)
            blocked_stats = summarize(blocked_requests)

            country_names = {}
            for country_code in set([country for country, _ in success_stats[2]] + [country for country, _ in blocked_stats[2]]):
                country_name = await get_country_name(country_code)
                country_names[country_code] = country_name if country_name else country_code

            def format_country_name(country_code):
                return country_names.get(country_code, country_code)

            count_text = f"<pre>👑 IP + NATION COUNT 👑\n\n"

            count_text += "💫 Successful Requests\n\n"
            count_text += f"Total requests: {success_stats[0]:,}\n"
            count_text += f"Total IPs: {success_stats[1]}\n"
            count_text += f"Total Nations: {success_stats[4]}\n\n"

            count_text += "IP Region (show top 10):\n"
            for country, ips in success_stats[2]:
                count_text += f"{format_country_name(country)}: {len(ips)}\n"
            count_text += "\n"

            count_text += "TOP ASN (show top 10):\n"
            for asn, count in success_stats[3]:
                count_text += f" ➥ {asn}\n"
            count_text += "\n"

            count_text += "💫 Blocked Requests\n\n"
            count_text += f"Total requests: {blocked_stats[0]:,}\n"
            count_text += f"Total IPs: {blocked_stats[1]}\n"
            count_text += f"Total Nations: {blocked_stats[4]}\n\n"

            count_text += "IP Region (show top 10):\n"
            for country, ips in blocked_stats[2]:
                count_text += f"{format_country_name(country)}: {len(ips)}\n"
            count_text += "\n"

            count_text += "TOP ASN (show top 10):\n"
            for asn, count in blocked_stats[3]:
                count_text += f" ➥ {asn}\n"
            count_text += "\n"

            count_text += "Thanks for using our service\n"

            count_text += "</pre>\n\n"

            count_text += f"⏰ Time Remaining: {remaining_time} seconds\n"

            if remaining_time <= 5:
                count_text = count_text.replace(f"⏰ Time Remaining: {remaining_time} seconds\n", "")

            count_text += f"🚗 Data from user: <a href='https://t.me/{user_name}'> {full_name}</a> 🚗\n"

            await context.bot.edit_message_text(
                chat_id=chat_id,
                message_id=message.message_id,
                text=count_text,
                parse_mode="HTML"
            )
            await asyncio.sleep(4)
            remaining_time -= 5

    except Exception as e:
        await context.bot.send_message(
            chat_id=chat_id,
            text=f"❌ An error occurred: {str(e)}",
            parse_mode="HTML"
        )

    finally:
        remove_running_server(user_id)
        await context.bot.delete_message(chat_id=chat_id, message_id=message.message_id)
        await context.bot.send_message(
            chat_id=chat_id,
            text=f"{count_text}",
            parse_mode="HTML"
        )   


async def handle_stats_clf(update: Update, context: ContextTypes.DEFAULT_TYPE, server_info, path):
    import asyncio
    from collections import defaultdict
    from datetime import datetime

    # Initialize user and chat info
    chat_id = update.effective_chat.id
    user = update.callback_query.from_user
    user_id = user.id
    user_name = user.username
    full_name = user.full_name
    language = load_user_language(user_id)

    # Send start message
    title = (
        f"🎬 <b>Bắt Đầu Ghi Nhận Tấn Công Của {server_info['name']} bởi @{user_name}</b>"
        if language == "vi" else
        f"🎬 <b>Start Recording Attack For {server_info['name']} by @{user_name}</b>"
    )
    message = await context.bot.send_message(chat_id=chat_id, text=title, parse_mode="HTML")

    # Timing setup
    start_time = datetime.utcnow()
    duration = 200
    remaining_time = duration

    try:
        while remaining_time > 0:
            loop_start_time = datetime.utcnow()
            current_time = datetime.utcnow()

            # Fetch blocked and allowed events
            blocked_events = await fetch_clfdata(update, user_id, server_info, start_time, current_time, path)
            allowed_events, _ = await fetch_passdata(update, user_id, server_info, start_time, current_time, path)

            # Aggregate counts
            allowed_requests = sum(evt.get('count', 1) for evt in allowed_events)
            bypassed_requests = sum(evt.get('count', 1) for evt in blocked_events if 'bypassed' in (evt.get('action') or ''))
            blocked_requests = sum(
                evt.get('count', 1)
                for evt in blocked_events
                if evt.get('action') not in (None, 'skip')
                and 'bypassed' not in (evt.get('action') or '')
                and evt.get('originResponseStatus') == 0
                and 'solved' not in (evt.get('action') or '')
            )
            total_count = allowed_requests + bypassed_requests + blocked_requests

            # Build report text
            count_text = "<pre>"
            count_text += f"🔰 Attack Report for: {server_info['name']} 🔰\n"
            count_text += f"Total Requests: {format_number(total_count)}\n"
            count_text += "╠" + "═"*36 + "╣\n"

            # Summary
            count_text += f"✔️ Successful: {format_number(allowed_requests + bypassed_requests)} ({format_percentage(allowed_requests + bypassed_requests, total_count)})\n"
            count_text += f"❌ Blocked: {format_number(blocked_requests)} ({format_percentage(blocked_requests, total_count)})\n"
            count_text += "╠" + "═"*36 + "╣\n\n"

            # Detailed blocked events
            count_text += "🛡️ Blocked Details:\n"
            for evt in blocked_events:
                action = evt.get('action')
                if action in (None, 'skip') or 'bypassed' in action or evt.get('originResponseStatus') != 0 or 'solved' in action:
                    continue
                # use evt directly since no 'dimensions'
                count_text += (
                    f"• Time: {evt.get('datetime','')}\n"
                    f"  - Rule: {evt.get('ruleId','N/A')} ({evt.get('ruleMessage','N/A')})\n"
                    f"  - Source: {translate_source(evt.get('source',''))}\n"
                    f"  - BotScore: {evt.get('botScore','-')}\n"
                    f"  - BotTags: {', '.join(evt.get('botDetectionTags', []))}\n"
                    f"  - Client: {evt.get('clientIP','')} | {evt.get('clientCountryName','')} | ASN {evt.get('clientAsn','')}\n"
                    f"  - Method/Protocol: {evt.get('clientRequestHTTPMethodName','')}/{evt.get('clientRequestHTTPProtocol','')}\n"
                    f"  - Path: {evt.get('clientRequestPath','')}?{evt.get('clientRequestQuery','')}\n"
                    f"  - Status E/O: {evt.get('edgeResponseStatus','')}/{evt.get('originResponseStatus','')}\n"
                )
                count_text += "│" + "─"*36 + "│\n"

            # Detailed allowed events breakdown by protocol/status
            count_text += "\n🔫 Allowed Details:\n"
            protocols = defaultdict(int)
            for evt in allowed_events:
                proto = evt.get('clientRequestHTTPProtocol','')
                status = evt.get('originResponseStatus', '')
                protocols[(proto, status)] += evt.get('count',1)
            for (proto, status), cnt in protocols.items():
                count_text += (
                    f"• Protocol: {proto} | Status: {status} | Count: {format_number(cnt)}\n"
                )
            count_text += "</pre>\n"

            # Time remaining and footer
            count_text += f"⏰ Time Remaining: {remaining_time}s\n"
            count_text += f"🚗 Data from: <a href='https://t.me/{user_name}'>{full_name}</a>\n"

            # Edit message
            await context.bot.edit_message_text(
                chat_id=chat_id,
                message_id=message.message_id,
                text=count_text,
                parse_mode="HTML"
            )

            # Sleep and decrement
            elapsed = (datetime.utcnow() - loop_start_time).total_seconds()
            await asyncio.sleep(4)
            remaining_time -= int(elapsed) + 4

    except Exception as e:
        await context.bot.send_message(chat_id=chat_id, text=f"Error during statistics handling: {str(e)}")
    finally:
        # Cleanup
        remove_running_server(user_id)
        await context.bot.delete_message(chat_id=chat_id, message_id=message.message_id)

        # Final summary send
        current_time = datetime.utcnow()
        events = await fetch_statistics(update, user_id, server_info, start_time, current_time, path)
        events2, _ = await fetch_statistics_pass(update, user_id, server_info, start_time, current_time, path, False)
        events3, _ = await fetch_statistics_pass(update, user_id, server_info, start_time, current_time, path, True)

        all_events = events + events2
        total_pass = sum(evt.get('count',1) for evt in events3)

        # Summarize by country and ASN
        country_ip_counts = defaultdict(set)
        asn_counts = defaultdict(int)
        for evt in all_events:
            country_ip_counts[evt.get('clientCountryName','')].add(evt.get('clientIP',''))
            asn_counts[evt.get('clientAsn','')] += evt.get('count',1)
        top_countries = sorted(country_ip_counts.items(), key=lambda x: len(x[1]), reverse=True)[:10]
        top_asns = sorted(asn_counts.items(), key=lambda x: x[1], reverse=True)[:10]

        country_summary = [f"{c}-{len(ips)}" for c, ips in top_countries]
        asn_summary = [f"{asn}-{cnt}" for asn, cnt in top_asns]

        source_counts = defaultdict(int)
        for evt in events:
            source_counts[evt.get('source','')] += evt.get('count',1)
        source_summary = [f"{s}-{cnt}" for s, cnt in source_counts.items()]
        if total_pass > 0:
            source_summary.append(f"pass-{total_pass}")

        # Send final messages and graphs
        await context.bot.send_message(chat_id=chat_id, text=count_text, parse_mode='HTML')
        await send_pre_graph_to_user(
            update, context, chat_id, user_id,
            server_info['name'], count_text,
            country_summary, asn_summary, source_summary, total_pass
        )

        
async def handle_stats_l4(update: Update, context: ContextTypes.DEFAULT_TYPE, server_info):
  chat_id = update.effective_chat.id
  user_name = update.callback_query.from_user.username
  language = load_user_language(update.effective_user.id)
  user_id = update.effective_user.id

  await context.bot.send_message(chat_id=chat_id, text=f"🎬 <b>Bắt Đầu Ghi Nhận Tấn Công Của {server_info['name']} bởi @{user_name}</b>" if language == "vi" else f"🎬 <b>Start Recording Attack For {server_info['name']} by @{user_name}</b>",parse_mode="HTML")
  time_start = int(time.mktime(datetime.utcnow().timetuple()))

  await asyncio.sleep(100)

  time_end = int(time.mktime(datetime.utcnow().timetuple()))

  await fetch_netdata(update, user_id, server_info['url'] , server_info['scope_nodes'] , time_start, time_end)

  remove_running_server(user_id)

  await summary_and_cleanup_l4(update, context, server_info['name'])


###############################################

async def top_users(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    language = load_user_language(update.effective_user.id)
    message_text = "🔥 <b>Chọn Loại Top Cần Xem</b>" if language == 'vi' else "🃏 <b>Choose Top Type</b>"
    buttons = [
        [
            InlineKeyboardButton("L4 DailyTOP", callback_data="layer4_daily_top"),
            InlineKeyboardButton("L4 HistoryTOP", callback_data="layer4_dstat_top")
        ],
        [
            InlineKeyboardButton("L7 DailyTOP", callback_data="layer7_daily_top"),
            InlineKeyboardButton("L7 HistoryTOP", callback_data="layer7_dstat_top")
        ],
        [InlineKeyboardButton("<< Back To Home", callback_data="backtohome")]
    ]
    reply_markup = InlineKeyboardMarkup(buttons)

    if update.callback_query:
        await update.callback_query.message.edit_text(message_text, reply_markup=reply_markup,parse_mode="HTML")
    else:
        await update.message.reply_text(message_text, reply_markup=reply_markup,parse_mode="HTML")

async def update_user_data(update, context, server_url):
  user_id = update.callback_query.from_user.id
  language = load_user_language(user_id)
  previous_value = load_data(user_id, 'previous_value')
  differences = load_data(user_id, 'differences') or []
  difference = 0
  try:
      new_value = await fetch_nginx_status(update, server_url)
      if new_value is not None and previous_value is not None:
          difference = new_value - previous_value
          differences.append(difference)
      else:
          previous_value = new_value

      save_log(user_id, server_url, difference)
      save_data(user_id, 'previous_value', new_value if 'new_value' in locals() else 0)
      save_data(user_id, 'differences', differences)

  except Exception as e:
      difference = -1
      differences.append(difference)
      save_data(user_id, 'differences', differences)
      save_log(user_id, server_url, difference)


async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
  query = update.callback_query
  await query.answer()
  data = query.data
  user_id = update.effective_user.id
  language = load_user_language(user_id)
  chat_id = update.effective_chat.id
  vip_users = load_vip_users()
  blocked_users = load_blocked_users()
  banned_users = load_banned_users()
  if data.startswith("layer7count_"):
      server_name = data.split("layer7count_")[1]
  elif data.startswith("layer4count_"):
      server_name = data.split("layer4count_")[1]
  elif data.startswith("clfcount_"):
      server_name = data.split("clfcount_")[1]
  else:
          server_name = data

  if data == "layer7_dstat":
    servers = load_servers()  
    await show_servers(update, context, servers, "layer7")
    return
  
  if user_id in banned_users:
    return

  if user_id in blocked_users:
    return

  if is_group_locked(chat_id) and update.effective_user.id not in admin_ids:
    return

  if query.data == 'see_my_plan':
      if str(user_id) in vip_users and has_valid_license(user_id):
          expiration_date = vip_users[str(user_id)]
          plan_message = f"<pre>𝗣𝗹𝗮𝗻 𝗗𝗲𝘁𝗮𝗶𝗹𝘀\n> Access to Aurologic-3TB ✅\n> Premium Statistics ✅\n> Plan Expires on: {expiration_date}\n⚜️ 𝗣𝗥𝗘𝗠𝗜𝗨𝗠 𝗣𝗟𝗔𝗡 ⚜️</pre>"
          buttons = [[InlineKeyboardButton("<< Back To Home", callback_data='backtohome')]]
          reply_markup = InlineKeyboardMarkup(buttons)
          await query.edit_message_text(text=plan_message, reply_markup=reply_markup, parse_mode="HTML")
          return
      if has_valid_license(user_id) == "no plan":
          plan_message = f"<pre>𝗣𝗹𝗮𝗻 𝗗𝗲𝘁𝗮𝗶𝗹𝘀\n> Access to Aurologic-3TB 🚫\n> Premium Statistics ✅\n> 𝗙𝗥𝗘𝗘 𝗣𝗟𝗔𝗡</pre>"
          buttons = [[InlineKeyboardButton("<< Back To Home", callback_data='backtohome')]]
          reply_markup = InlineKeyboardMarkup(buttons)
          await query.edit_message_text(text=plan_message, reply_markup=reply_markup, parse_mode="HTML")
          return
      if not has_valid_license(user_id):
        expiration_date = vip_users[str(user_id)]
        plan_message = f"<pre>𝗣𝗹𝗮𝗻 𝗗𝗲𝘁𝗮𝗶𝗹𝘀\n> Access to Aurologic-3TB ⚠️\n> Premium Statistics ✅\n> Plan Expires on: {expiration_date}\n❗️ 𝗘𝗫𝗣𝗜𝗥𝗘𝗗 ❗️</pre>"
        buttons = [[InlineKeyboardButton("<< Back To Home", callback_data='backtohome')]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.edit_message_text(text=plan_message, reply_markup=reply_markup, parse_mode="HTML")
        return 

  if is_maintenance_mode() and update.effective_user.id not in admin_ids:
    await context.bot.send_message(chat_id=update.callback_query.message.chat.id, text="⚠️ Bot Maintenance ⚠️")
    return

  if data == "cloudflare_dstat":
    servers = load_servers_clf()  
    await show_servers_clf(update, context, servers)
    return

  if data == "private_captcha_count_ip" and user_id in PRIVATE_DSTAT_USER_ID:
    await captcha_count_ip_buttons(update, context, language)
    return

  if data == "layer4_dstat":
    await protection_buttons(update, context, language)
    return

    # NÚT ĐỔI QUA GBPS or PPS CỦA HIST
  if data.startswith("show_packet_top_"):
    query_data = data.split('_')
    server_name = query_data[-2]
    protected = query_data[-1]
    await show_top_for_server_l4(update, context, server_name, protected, 'packet')
    return

    # NÚT ĐỔI QUA GBPS or PPS CỦA HIST
  if data.startswith("show_received_top_"):
    query_data = data.split('_')
    server_name = query_data[-2]
    protected = query_data[-1]
    await show_top_for_server_l4(update, context, server_name, protected, 'received')
    return

    # NÚT ĐỔI QUA GBPS or PPS CỦA DAILY
  if data.startswith("dailyshow_packet_top_"):
    query_data = data.split('_')
    server_name = query_data[-2]
    protected = query_data[-1]
    await show_daily_top_for_server_l4(update, context, server_name, protected, 'packet')
    return

    # NÚT ĐỔI QUA GBPS or PPS CỦA DAILY
  if data.startswith("dailyshow_received_top_"):
    query_data = data.split('_')
    server_name = query_data[-2]
    protected = query_data[-1]
    await show_daily_top_for_server_l4(update, context, server_name, protected, 'received')
    return

    # NÚT ĐỔI QUA MAX HOẶC TOTAL CỦA HIST
  if data.startswith("show_max_top_"):
    server_name = data.split("show_max_top_")[1]
    await show_top_for_server(update, context, server_name, 'max')
    return
  if data.startswith("show_total_top_"):
    server_name = data.split("show_total_top_")[1]
    await show_top_for_server(update, context, server_name, 'total')
    return

    # NÚT ĐỔI QUA MAX HOẶC TOTAL CỦA DAILY
  if data.startswith("dailyshow_max_top_"):
    server_name = data.split("dailyshow_max_top_")[1]
    await show_daily_top_for_server(update, context, server_name, 'max')
    return

    # NÚT ĐỔI QUA MAX HOẶC TOTAL CỦA DAILY
  if data.startswith("dailyshow_total_top_"):
    server_name = data.split("dailyshow_total_top_")[1]
    await show_daily_top_for_server(update, context, server_name, 'total')
    return

  if data == "back_to_protected_type":
    await protection_buttons(update, context, language) 
    return

  if data == "l4protected_false":
      servers = load_filtered_servers(protected=False) 
      await show_servers_l4(update, context, servers, "layer4")
      return

  if data == "backtohome":
      name = update.effective_user.first_name
      language = load_user_language(user_id)
      welcome_message = "👋 Welcome to AIKO 2.0 – Use the bot for <b>FREE</b>! Questions or feedback? Contact an Administrator 👾"
      buttons = [
          [
              InlineKeyboardButton("Layer 4 Dstat", callback_data='layer4_dstat'),
              InlineKeyboardButton("Layer 7 Dstat", callback_data='layer7_dstat')
          ],
          [
              InlineKeyboardButton("Cloudflare Statistics Dstat", callback_data='cloudflare_dstat'),
          ],
          [
              InlineKeyboardButton("Leaderboard", callback_data='leaderboard')
          ],
          [
              InlineKeyboardButton("Setting", callback_data='setting'),
              InlineKeyboardButton("Contact Admin", url="https://t.me/KeAiAiko")
          ]
      ] if language == "en" else [
          [
              InlineKeyboardButton("Layer 4 Dstat", callback_data='layer4_dstat'),
              InlineKeyboardButton("Layer 7 Dstat", callback_data='layer7_dstat')
          ],
          [
              InlineKeyboardButton("Dstat Từ Dữ Liệu Cloudflare", callback_data='cloudflare_dstat'),
          ],
          [
              InlineKeyboardButton("Bảng xếp hạng", callback_data='leaderboard')
          ],
          [
              InlineKeyboardButton("Cài đặt", callback_data='setting'),
              InlineKeyboardButton("Liên hệ Admin", url="https://t.me/KeAiAiko")
          ]
      ]
      if user_id in PRIVATE_DSTAT_USER_ID:
          buttons.append([InlineKeyboardButton("Nation + Count IP", callback_data='private_captcha_count_ip')])
      buttons.append([InlineKeyboardButton("View My Plan", callback_data='see_my_plan')])
      reply_markup = InlineKeyboardMarkup(buttons)

      await query.edit_message_text(text=welcome_message, reply_markup=reply_markup,parse_mode="HTML")
      return

  if data == "setting":
      if language == 'vi':
          buttons = [
              [
                  InlineKeyboardButton("Tiếng Việt", callback_data='lang_vi'),
                  InlineKeyboardButton("Tiếng Anh", callback_data='lang_en')
              ],
              [
                  InlineKeyboardButton("<< Back To Home", callback_data='backtohome')
              ],
          ]
          message_text = "🃏 <b>Chọn Ngôn Ngữ Của Bạn</b>\n" + "➖" * 12
      else:
          buttons = [
              [
                  InlineKeyboardButton("Vietnamese", callback_data='lang_vi'),
                  InlineKeyboardButton("English", callback_data='lang_en')
              ],
              [
                  InlineKeyboardButton("<< Back To Home", callback_data='backtohome')
              ],
          ]
          message_text = "🃏 <b>Choose Your Language</b>\n" + "➖" * 12 

      reply_markup = InlineKeyboardMarkup(buttons)
      await query.edit_message_text(text=message_text, reply_markup=reply_markup,parse_mode="HTML")
      return


  if data == "l4protected_true":
      servers = load_filtered_servers(protected=True) 
      await show_servers_l4(update, context, servers, "layer4")
      return

  if data == "leaderboard":
      await top_users(update, context)
      return


  if data == "l4protected_true":
      servers = load_filtered_servers(protected=True) 
      await show_servers_l4(update, context, servers, "layer4")
      return

  if data == "leaderboard":
      await top_users(update, context)
      return

  if data == "layer7_dstat_top":
      servers = load_servers() 
      await show_top_servers_l7(update, context, servers, "layer7")
      return

  if data == "layer7_daily_top":
      servers = load_servers() 
      await daily_top_servers_l7(update, context, servers, "layer7")
      return

      # NÚT SHOW UN or PRO CHO HIST
  if data == "layer4_dstat_top":
      await protection_buttons_for_top(update, context, language)
      return

      # NÚT SHOW UN or PRO CHO DAILY
  if data == "layer4_daily_top":
      await protection_buttons_daily_top(update, context, language)
      return

      # TỪ SV L4 trở về nút UN or PRO
  if data == "back_to_protected_type_top":
      await protection_buttons_for_top(update, context, language)
      return

      # TỪ SV L4 trở về nút UN or PRO
  if data == "back_to_protected_type_daily_top":
      await protection_buttons_daily_top(update, context, language)
      return

     # DAILY TOP CHỌN NÚT PRO OR UN
  if data == "topl4protected_false":
      servers = load_filtered_servers(protected=False) 
      await show_top_servers_l4(update, context, servers, "un")
      return

    # HIST TOP CHỌN NÚT PRO OR UN
  if data == "dailytopl4protected_false":
      servers = load_filtered_servers(protected=False) 
      await daily_top_servers_l4(update, context, servers, "un")
      return
     # DAILY TOP CHỌN NÚT PRO OR UN
  if data == "dailytopl4protected_true":
      servers = load_filtered_servers(protected=True) 
      await daily_top_servers_l4(update, context, servers, "pro")
      return

     # HIST TOP CHỌN NÚT PRO OR UN
  if data == "topl4protected_true":
      servers = load_filtered_servers(protected=True) 
      await show_top_servers_l4(update, context, servers, "pro")
      return
     # HIST TOP CHỌN SV ĐỂ XEM
  if data.startswith("l7top_"):
      server_name = data.split("_")[1]
      await show_top_for_server(update, context, server_name)
      return
      # NÚT ĐỂ COI TOP CỦA DAILY
  if data.startswith("dailyl7top_"):
      server_name = data.split("_")[1]
      await show_daily_top_for_server(update, context, server_name)
      return

      # NÚT ĐỂ COI TOP CỦA HIST
  if data.startswith("l4topun_"):
      server_name = data.split("_")[1]
      await show_top_for_server_l4(update, context, server_name, "un")
      return

      # NÚT ĐỂ COI TOP CỦA HIST
  if data.startswith("l4toppro_"):
      server_name = data.split("_")[1]
      await show_top_for_server_l4(update, context, server_name, "pro")
      return

      # NÚT ĐỂ COI TOP CỦA DAILY
  if data.startswith("dailyl4topun_"):
      server_name = data.split("_")[1]
      await show_daily_top_for_server_l4(update, context, server_name, "un")
      return

      # NÚT ĐỂ COI TOP CỦA DAILY
  if data.startswith("dailyl4toppro_"):
      server_name = data.split("_")[1]
      await show_daily_top_for_server_l4(update, context, server_name, "pro")
      return

  if data.startswith('lang_'):
    language = data.split('_')[1]
    save_user_language(query.from_user.id, language)
    await context.bot.send_message(chat_id=update.callback_query.message.chat.id, text=f"🃏 <b>Language Set To {'English 🇺🇸' if language == 'en' else 'Tiếng Việt 🇻🇳'}</b>", parse_mode='HTML')
    add_user_to_subscribed(user_id)
    return

  if data == "back_to_dstat_type":
    await top_users(update, context)
    return

  if data == "back_to_top_users":
    servers = load_servers() 
    await show_top_servers_l7(update, context, servers, "layer7")
    return

  if data == "back_to_daily_top_users":
    servers = load_servers() 
    await daily_top_servers_l7(update, context, servers, "layer7")
    return

    #NÚT BACK TỪ COI TOP VỀ SHOW SERVER HIST
  if data == "back_to_top_users_l4_un":
    servers = load_filtered_servers(protected=False) 
    await show_top_servers_l4(update, context, servers, "un")
    return

    #NÚT BACK TỪ COI TOP VỀ SHOW SERVER DAILY
  if data == "dailyback_to_top_users_l4_un":
    servers = load_filtered_servers(protected=False) 
    await daily_top_servers_l4(update, context, servers, "un")
    return

    #NÚT BACK TỪ COI TOP VỀ SHOW SERVER HIST
  if data == "back_to_top_users_l4_pro":
    servers = load_filtered_servers(protected=True) 
    await show_top_servers_l4(update, context, servers, "pro")
    return

    #NÚT BACK TỪ COI TOP VỀ SHOW SERVER DAILY
  if data == "dailyback_to_top_users_l4_pro":
    servers = load_filtered_servers(protected=True) 
    await daily_top_servers_l4(update, context, servers, "pro")
    return

  if data == "back_to_dstatcount_type":
    await count(update, context)
    return

  current_server = load_running_server(user_id)

  if current_server:
    current_server_name = current_server.get('server_name')
    if current_server_name != server_name or current_server_name == server_name:
        await context.bot.send_message(
            chat_id=chat_id,
            text="<b>Bạn đang sử dụng một server. Vui lòng hoàn thành trước khi sử dụng server khác</b>" if language == "vi" else "<b>You are already using a server. Please complete that before using another one</b>",
            parse_mode="HTML"
        )
        return

  server_limit = 1 if server_name in ["Cloudflare-Entreprise", "WP-ENTREPRISE"] else 1
  if count_server_usage(server_name) >= server_limit and (not current_server or current_server_name != server_name):
    try:
        with open('server_running.json', 'r', encoding='utf-8') as file:
            server_running = json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        server_running = {}

    servers_to_remove = []
    for user_id, srv in server_running.items():
        remaining_time = int((datetime.strptime(srv['expiration_time'], '%Y-%m-%d %H:%M:%S') - datetime.utcnow()).total_seconds())

        if remaining_time <= -150:
            servers_to_remove.append(user_id)
        elif remaining_time >= 0:
            srv['expiration_time_display'] = "Generating Result..."

    for user_id in servers_to_remove:
        del server_running[user_id]

    with open('server_running.json', 'w', encoding='utf-8') as file:
        json.dump(server_running, file, ensure_ascii=False, indent=4)


    if count_server_usage(server_name) >= server_limit:
        running_servers_info = "\n".join([
            f"{srv['full_name']} --> <b>{srv['server_name']}</b> ({int((datetime.strptime(srv['expiration_time'], '%Y-%m-%d %H:%M:%S') - datetime.utcnow()).total_seconds())}s remaining)"
            for srv in server_running.values()
        ])

        response_text = (
            f"<b>🃏 Server này đang được người khác sử dụng. Vui lòng chọn server khác</b>\n\n"
            f"<b>🃏 Các server đang được sử dụng</b>\n{running_servers_info}"
            if language == "vi"
            else
            f"<b>🃏 This server is currently in use by another user. Please select a different server</b>\n\n"
            f"<b>🃏 Servers currently in use:</b>\n{running_servers_info}"
        )
        
        for srv in server_running.values():
            remaining_time = int((datetime.strptime(srv['expiration_time'], '%Y-%m-%d %H:%M:%S') - datetime.utcnow()).total_seconds())
            if remaining_time <= 0:
                response_text = response_text.replace(f"{remaining_time}s remaining", "Generating Result...")

        await context.bot.send_message(
            chat_id=update.callback_query.message.chat.id,
            text=response_text,
            parse_mode="HTML"
        )
        return
  
  if data.startswith('captcha_'):
      random_path = generate_random_query()
      if user_id not in PRIVATE_DSTAT_USER_ID:
          return
      message_text = (f"Server: 🃏<b>IP + NATION COUNT</b> 🃏\n"
                      f"⤷ Mục Tiêu (Ấn vào để copy URL): <code>https://weak.dstateuis.site/{random_path}</code>\n"
                      f"⤷ Ghi dữ liệu trong: <b>200s</b>") if language == "vi" else (f"Server Name: 🃏<b>IP + NATION COUNT</b> 🃏\n"
                      f"⤷ Target (Click to copy URL): <code>https://weak.dstateuis.site/{random_path}</code>\n"
                      f"⤷ Statistics Duration: <b>200s</b>")

      if user_id in PRIVATE_DSTAT_USER_ID:
          save_running_server(user_id, server_name, update.effective_user.full_name, 200)
          await query.edit_message_text(text=message_text, parse_mode='HTML')
          asyncio.create_task(handle_stats_captcha(update, context, random_path))
      else:
          await query.edit_message_text(text="Không tìm thấy thông tin Server" if language == "vi" else "Server infomation not found", parse_mode='HTML')


  if data.startswith('clfcount_'):
      servers = load_servers_clf()
      random_path = generate_random_query()
      server_info = next((server for server in servers if server['name'] == server_name), None)

      if server_info is None:
          return
      message_text = (f"Server: 🎉<b>{server_info['name']}</b> 🎉\n"
                      f"⤷ Mục Tiêu (Ấn vào để copy URL): 📋 <code>{server_info['target']}{random_path}</code>📋\n"
                      f"⤷ Ghi dữ liệu trong: ⏱<b>{server_info['time']}s</b>") if language == "vi" else (f"Server Name: 🎉<b>{server_info['name']}</b> 🎉\n"
                      f"⤷ Target (Click to copy URL): <code>{server_info['target']}{random_path}</code>\n"
                      f"⤷ Statistics Duration: ⏱<b>{server_info['time']}s</b>")


      if server_info:
          save_running_server(user_id, server_name, update.effective_user.full_name, 200)
          await query.edit_message_text(text=message_text, parse_mode='HTML')
          asyncio.create_task(handle_stats_clf(update, context, server_info,random_path))
      else:
          await query.edit_message_text(text="Không tìm thấy thông tin Server" if language == "vi" else "Server infomation not found", parse_mode='HTML')


  if data.startswith('layer7count_'):
    servers = load_servers()
    server_info = next((server for server in servers if server['name'] == server_name), None)
    if server_info is None:
        return
        
    if server_name in ["Cloudflare-Pro", "Cloudflare-Business"]:
        servers = load_servers_clf()
        random_path = generate_random_query()
        svclf_info = next((server for server in servers if server['name'] == server_name), None)
        if svclf_info is None:
            return
        message_text = (f"Server: 🃏<b>{svclf_info['name']}</b> 🃏\n"
                        f"⤷ Mục Tiêu (Ấn vào để copy URL): <code>{svclf_info['target']}{random_path}</code>\n"
                        f"⤷ Ghi dữ liệu trong: <b>{svclf_info['time']}s</b>") if language == "vi" else (f"Server Name: 🃏<b>{svclf_info['name']}</b> 🃏\n"
                        f"⤷ Target (Click to copy URL): <code>{svclf_info['target']}{random_path}</code>\n"
                        f"⤷ Statistics Duration: <b>{svclf_info['time']}s</b>")
        if svclf_info:
              save_running_server(user_id, server_name, update.effective_user.full_name, 200)
              await query.edit_message_text(text=message_text, parse_mode='HTML')
              asyncio.create_task(handle_stats_clf(update, context, svclf_info,random_path))
              return
        else:
              await query.edit_message_text(text="Không tìm thấy thông tin Server" if language == "vi" else "Server infomation not found", parse_mode='HTML')
              return

    if server_name == "TOPSHIELD":
        message_text = (f"Server: 🃏<b>{server_info['name']}</b> 🃏\n"
                        f"⤷ Mục Tiêu (Ấn vào để copy URL): <code>{server_info['target']}</code>\n"
                        f"⤷ Ghi dữ liệu trong: <b>{server_info['time']}s</b>") if language == "vi" else (f"Server Name: 🃏<b>{server_info['name']}</b> 🃏\n"
                        f"⤷ Target (Click to copy URL): <code>{server_info['target']}</code>\n"
                        f"⤷ Statistics Duration: <b>{server_info['time']}s</b>")
        if server_info:
            save_running_server(user_id, server_name, update.effective_user.full_name, server_info['time'])
            await query.edit_message_text(text=message_text, parse_mode='HTML')
            asyncio.create_task(handle_topshield_stats(update, context, server_info,server_info['time']))
            return
        else:
            await query.edit_message_text(text="Không tìm thấy thông tin Server" if language == "vi" else "Server infomation not found", parse_mode='HTML')
            return

    parsed_url = urlparse(server_info['target'])
    simplified_url = f"{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}"

    message_text = (f"Server: 🃏<b>{server_info['name']}</b> 🃏\n"
                    f"⤷ Mục Tiêu (Ấn vào để copy URL): <code>{simplified_url}</code>\n"
                    f"⤷ Loại Bảo Vệ: <b>{server_info['protection_type']}</b>\n"
                    f"⤷ Ghi dữ liệu trong: <b>{server_info['time']}s</b>") if language == "vi" else (f"Server Name: 🃏<b>{server_info['name']}</b> 🃏\n"
                    f"⤷ Target (Click to copy URL): <code>{simplified_url}</code>\n"
                    f"⤷ Protection Type: <b>{server_info['protection_type']}</b>\n"
                    f"⤷ Statistics Duration: <b>{server_info['time']}s</b>")

    if server_info:
      save_running_server(user_id, server_name, update.effective_user.full_name, server_info['time'])
      await query.edit_message_text(text=message_text, parse_mode='HTML')
      asyncio.create_task(handle_stats(update, context, server_info, server_info['time']))
    else:
      await query.edit_message_text(text="Không tìm thấy thông tin Server" if language == "vi" else "Server infomation not found", parse_mode='HTML')



  if data.startswith('layer4count_'):
      servers = load_l4servers()
      server_info = next((server for server in servers if server['name'] == server_name), None)
      if server_info is None:
          return
      target = server_info['ip']
      if server_info['name'] == "Aurologic-3TB":
            if not has_valid_license(user_id):
                await query.edit_message_text(text="🃏 <b>Your Plan Has Expired</b>",parse_mode="HTML")
                return
            elif has_valid_license(user_id) == "no plan":
                await query.edit_message_text(text="🃏 <b>Please Purchase Plan To Use Vip Service</b>",parse_mode="HTML")
                return
            if query.message.chat.type != 'private':
                await query.message.reply_text("🃏 <b>Use This Server In Private Chat With Bot</b>",parse_mode="HTML")
                return
            message_text = (f"Server Name: 🃏<b>{server_info['name']}</b> 🃏\n"
                  f"⤷ Target (Click to copy URL): <code>{target}</code>\n⤷ Port: TCP: <b>22</b> | UDP: <b>53</b> <b></b>\n"
                  f"⤷ Protection Type: <b>{server_info['protection_type']}</b>\n"
                  "⤷ Statistics Duration: <b>200s</b>")
            save_running_server(user_id, server_name, update.effective_user.full_name, 200)
            await query.edit_message_text(text=message_text, parse_mode='HTML')
            asyncio.create_task(handle_stats_aurologic(update, context, server_info))
            return

      message_text = (f"Server: 🎉<b>{server_info['name']}</b> 🎉\n"
                      f"⤷ Mục Tiêu (Ấn vào để copy URL): <code>{target}</code> | Port: <b>{server_info['port']}</b>\n"
                      f"⤷ Loại Bảo Vệ: <b>{server_info['protection_type']}</b>\n"
                      "⤷ Ghi dữ liệu trong: <b>100s</b>") if language == "vi" else (f"Server Name: 🃏<b>{server_info['name']}</b> 🃏\n"
                      f"⤷ Target (Click to copy URL): <code>{target}</code> | Port: <b>{server_info['port']}</b>\n"
                      f"⤷ Protection Type: <b>{server_info['protection_type']}</b>\n"
                      "⤷ Statistics Duration: <b>100s</b>")

      if server_info:
        save_running_server(user_id, server_name, update.effective_user.full_name, 60)
        await query.edit_message_text(text=message_text, parse_mode='HTML')
        asyncio.create_task(handle_stats_l4(update, context, server_info))
      else:
        await query.edit_message_text(text="Không tìm thấy thông tin Server" if language == "vi" else "Server infomation not found", parse_mode='HTML')



from apscheduler.schedulers.asyncio import AsyncIOScheduler

scheduler = AsyncIOScheduler()

async def send_ads_message(context: ContextTypes.DEFAULT_TYPE):
    chat_id = -1002212694900
    await context.bot.send_message(
        chat_id=chat_id,
        text=(
            "🚨 <b>AIKO LOGS Alert</b> 🚨\n\n"
            "──────────────────────────────\n\n"
            "🔥 <b>Premium Advertisement</b> 🔥\n\n"
            "──────────────────────────────\n\n"
            "🏅 <b>Top-Tier L7/L4 Solutions:</b>\n"
            "- STRESSLAB: Experience the ultimate in DDoS with our unmatched technology.\n"
            "<a href='https://t.me/stresslabpower'>Join our [Telegram](#) for exclusive updates and support.</a>\n"
            "<a href='https://weak1011.store/'>- STRESSLAB Website: Click here to explore cutting-edge solutions that lead the industry.</a>\n\n"
            "🏅 <b>OVERLOAD.SU - Botnet Powered Stresser:</b>\n"
            "- Offering L4/L7 raw power with 40GB+ bandwidth and 200k RPS per concurrent attack.\n"
            "<a href='https://overload.su/'>Visit OVERLOAD.SU for premium bypasses and unbeatable performance.</a>\n\n"
            "──────────────────────────────"
        ),
        parse_mode="HTML"
    )

async def ads_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id

    if user_id not in admin_ids:
        await update.message.reply_text("You don't have permission to use this command.")
        return
    await send_ads_message(context)

    job = scheduler.get_job(f"ads_{chat_id}")
    if job is None:
        scheduler.add_job(send_ads_message, 'interval', minutes=60, args=[context], id=f"ads_{chat_id}")
        await update.message.reply_text("Advertisements have started. Messages will be sent every 30 minutes.")
    else:
        await update.message.reply_text("Advertisements are already running.")

async def stop_ads_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id

    if user_id not in admin_ids:
        await update.message.reply_text("You don't have permission to use this command.")
        return
    job = scheduler.get_job(f"ads_{chat_id}")
    if job:
        scheduler.remove_job(f"ads_{chat_id}")
        await update.message.reply_text("Advertisements have been stopped.")
    else:
        await update.message.reply_text("No advertisements are running.")


async def restart(update: Update, context):
    chat_id = update.message.chat_id
    await context.bot.send_message(chat_id=chat_id, text="<blockquote><b>Bot has been restarted successfully 🔌</b></blockquote>",parse_mode='HTML')

    await asyncio.sleep(1)

    os._exit(0)

async def main():
    scheduler.start()
    await asyncio.Event().wait()  # Keeps the loop alive


app = ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("noti", send_notification))
app.add_handler(CommandHandler("add", add_server))
app.add_handler(CommandHandler("l4add", add_server_l4))
app.add_handler(CommandHandler("rm", remove_server))
app.add_handler(CommandHandler("l4rm", remove_server_l4))
app.add_handler(CommandHandler("sv", list_servers))
app.add_handler(CallbackQueryHandler(button_callback))
app.add_handler(CommandHandler("clr", clr))
app.add_handler(CommandHandler("del", delete_ranking))
app.add_handler(CommandHandler("l4del", delete_ranking_l4))
app.add_handler(CommandHandler("reset", reset_rank))
app.add_handler(CommandHandler("ping", show_server_status))
app.add_handler(CommandHandler("license", license_command))
app.add_handler(CommandHandler("key", key_command))
app.add_handler(CommandHandler("ban", ban))
app.add_handler(CommandHandler("unban", unban))
app.add_handler(CommandHandler("lock", lock_group))
app.add_handler(CommandHandler("unlock", unlock_group))
app.add_handler(CommandHandler("fakel7", fake_l7))
app.add_handler(CommandHandler("fakel4", fake_l4))
app.add_handler(CommandHandler("maintenance", maintenance_mode))
app.add_handler(CommandHandler('ads', ads_command))
app.add_handler(CommandHandler('stopads', stop_ads_command))
app.add_handler(CommandHandler('restart', restart))
print("OK NHE")
app.run_polling()



