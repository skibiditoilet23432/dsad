import json
from datetime import datetime
import os
from datetime import datetime, timedelta

from graph import send_graph_to_user, send_graphl4_to_user

group_id = -1002166455565
USER_IDS_FILE = 'user_ids.json'

#######  FORMAT FUNCTION  #######
def format_data_rate(kbps):
    if kbps >= 1000**3:  
        return f"{kbps / 1000**3:.1f} Tbps"
    elif kbps >= 1000**2:  
        return f"{kbps / 1000**2:.1f} Gbps"
    elif kbps >= 1000:  
        return f"{kbps / 1000:.1f} Mbps"
    else:  
        return f"{kbps:.1f} Kbps"

def format_data_total(kbps):
    if kbps >= 1000**3:  
        return f"{kbps / 1000**3:.1f} Tb"
    elif kbps >= 1000**2:  
        return f"{kbps / 1000**2:.1f} Gb"
    elif kbps >= 1000:  
        return f"{kbps / 1000:.1f} Mb"
    else:  
        return f"{kbps:.1f} Kb"

def format_number(number):
  if number >= 1000000:
      return f"{number / 1000000:.1f}M"
  elif number >= 1000:
      return f"{number / 1000:.1f}K"
  elif number >= 1000000000:
      return f"{number / 1000000000:,1f}T"
  else:
      return str(number)

def format_percentage(part, whole):
    return f"{(part / whole * 100):.2f}%" if whole != 0 else "0%"

def translate_source(source):
    if source.startswith('firewallCustom'):
        return 'Custom Rules'
    elif source.startswith('m'):
        return 'Managed Ruleset'
    elif source.startswith('s'):
        return 'Security Level'
    elif source.startswith('r'):
        return 'Rate Limit'
    elif source.startswith('l7'):
        return 'HTTP DDoS'
    elif source.startswith('bic'):
        return 'Browser Integrity Check'
    elif source.startswith('botFight'):
        return 'Bot Fight Mode'
    elif source.startswith('firewallManaged'):
        return 'Managed Rules'
    else:
        return source

def translate_action(action):
    translations = {
        "managed_challenge_non_interactive_solved": "Managed Challenge Bypassed",
        "managed_challenge_interactive_solved": "Managed Challenge Bypassed",
        "challenge_bypassed": "Interactive Challenge Bypassed",
        "skip": "Skip",
        "managed_challenge_bypassed": "Managed Challenge Bypassed",
        "challenge_solved": "Interactive Challenge Bypassed",
        "challenge": "Interactive Challenge",
        "block": "Blocked",
        "jschallenge": "JS Challenge",
        "managed_challenge": "Managed Challenge",
        "jschallenge_solved": "JS Challenge Bypassed"
    }
    return translations.get(action, action)

#######  LOADING & ADDING FUNCTION  #######
def count_server_usage(server_name):
    running_servers = load_all_running_servers()
    return sum(1 for server in running_servers.values() if server['server_name'] == server_name)

def load_all_running_servers():
    try:
        with open('server_running.json', 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        return {}

def add_user_to_subscribed(user_id):
  try:
      with open("sub_users.json", "r") as file:
          subscribed_users = json.load(file)
  except FileNotFoundError:
      subscribed_users = []
  if user_id not in subscribed_users:
      subscribed_users.append(user_id)
      with open("sub_users.json", "w") as file:
          json.dump(subscribed_users, file)

def load_user_language(user_id):
  try:
      with open('user_languages.json', 'r') as file:
          data = json.load(file)
          return data.get(str(user_id), "en")  
  except (FileNotFoundError, json.JSONDecodeError):
      return "en"  

def load_running_server(user_id):
    running_servers = load_all_running_servers()
    return running_servers.get(str(user_id))

def load_servers_from_file(file_path):
    try:
        with open(file_path, 'r') as file:
            data = json.load(file)
            return data.get('servers', [])
    except FileNotFoundError:
        return []

def load_servers():
  try:
      with open('servers.json', 'r') as file:
          data = json.load(file)
          return data.get('servers', [])
  except FileNotFoundError:
      return []

def load_servers_clf():
  try:
      with open('clf_sv.json', 'r') as file:
          data = json.load(file)
          return data.get('servers', [])
  except FileNotFoundError:
      return []
      

def load_l4servers():
  try:
      with open('l4_servers.json', 'r') as file:
          data = json.load(file)
          return data.get('servers', [])
  except FileNotFoundError:
      return []

def load_filtered_servers(protected=True):
    servers = load_l4servers()
    if protected:
        return [server for server in servers if server.get('protected')]
    else:
        return [server for server in servers if not server.get('protected')]

def load_data(user_id, key):
  try:
      with open(f"{user_id}_data.json", 'r') as file:
          data = json.load(file)
          return data.get(key)
  except (FileNotFoundError, json.JSONDecodeError):
      return None

def load_user_ids():
    with open(USER_IDS_FILE, 'r') as file:
        return json.load(file)

def save_user_ids(user_ids):
    with open(USER_IDS_FILE, 'w') as file:
        json.dump(user_ids, file)
        
def load_vip_users():
    with open('vip_users.json', 'r') as f:
        return json.load(f)
        
def load_blocked_users():
    try:
        with open('blocked.json', 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        return {}

def save_blocked_user(user_id, user_name, full_name):
    blocked_users = load_blocked_users()
    blocked_users[user_id] = {
        "username": user_name,
        "full_name": full_name,
        "blocked_time": datetime.utcnow().isoformat()
    }
    with open('blocked.json', 'w') as file:
        json.dump(blocked_users, file)

#######  SAVE & REMOVE FUNCTION  #######
def save_user_language(user_id, language):
  try:
      with open('user_languages.json', 'r+') as file:
          data = json.load(file)
  except FileNotFoundError:
      data = {}
  except json.JSONDecodeError:
      data = {}

  data[str(user_id)] = language

  with open('user_languages.json', 'w') as file:
      json.dump(data, file, indent=4)

def save_running_server(user_id, server_name, full_name, duration):
    running_servers = load_all_running_servers()
    expiration_time = datetime.utcnow() + timedelta(seconds=duration)
    running_servers[str(user_id)] = {
        "server_name": server_name,
        "full_name": full_name,
        "expiration_time": expiration_time.strftime("%Y-%m-%d %H:%M:%S")
    }
    with open('server_running.json', 'w') as file:
        json.dump(running_servers, file)

def save_servers(servers):
  with open('servers.json', 'w') as f:
      json.dump(servers, f, indent=4)
      
def remove_running_server(user_id):
    running_servers = load_all_running_servers()
    if str(user_id) in running_servers:
        del running_servers[str(user_id)]
        with open('server_running.json', 'w') as file:
            json.dump(running_servers, file)

def save_netdata(user_id, key, new_entry):
    try:
        with open(f"{user_id}_data_l4.json", 'r+') as file:
            try:
                data = json.load(file)
            except json.JSONDecodeError:
                data = {}
            if key not in data:
                data[key] = []
            data[key].append(new_entry)
            file.seek(0)
            json.dump(data, file, indent=4)
            file.truncate()
    except FileNotFoundError:
        with open(f"{user_id}_data_l4.json", 'w') as file:
            json.dump({key: [new_entry]}, file, indent=4)

def save_data(user_id, key, value):
  try:
      with open(f"{user_id}_data.json", 'r+') as file:
          try:
              data = json.load(file)
          except json.JSONDecodeError:
              data = {}
          data[key] = value
          file.seek(0)
          json.dump(data, file, indent=4)
          file.truncate()
  except FileNotFoundError:
      with open(f"{user_id}_data.json", 'w') as file:
          json.dump({key: value}, file, indent=4)
#######  CHECKING FUNCTION  #######

def is_user_subscribed(user_id):
  try:
      with open("sub_users.json", "r") as file:
          subscribed_users = json.load(file)
  except FileNotFoundError:
      subscribed_users = []
  return user_id in subscribed_users

#######  SAVE & SEND LOG FUNCTION  #######
def save_log(user_id, server_name, rps):
  log_file = f"{user_id}_logs.json"
  log_entry = {
      'datetime': datetime.now().isoformat(),
      'server': server_name,
      'rps': rps
  }
  try:
      with open(log_file, 'r+') as file:
          logs = json.load(file)
          logs.append(log_entry)
          file.seek(0)
          json.dump(logs, file, indent=4)
  except FileNotFoundError:
      with open(log_file, 'w') as file:
          json.dump([log_entry], file, indent=4)

async def send_log_to_user(context, chat_id, user_id, server_name, user_name):
  log_file = f"{user_id}_logs.json"
  language = load_user_language(user_id)
  try:
      with open(log_file, 'r') as file:
          logs = json.load(file)
          log_messages = [f"Requests ghi nhận của {server_name}"] if language == "vi" else [f"Attack Logs on {server_name}"]
          for log in logs:
              log_messages.append(f"{log['datetime']} | Rps: {log['rps']}")
          log_message_text = "\n".join(log_messages) + f"\nBy @{user_name}"

          await context.bot.send_message(chat_id=chat_id, 
                                         text=f"```\n{log_message_text}\n```", 
                                         parse_mode='MarkdownV2')
  except FileNotFoundError:
      await context.bot.send_message(chat_id=chat_id, 
                                     text="Không tìm thấy bản ghi nào" if language == "vi" else "No attack logs found")


#######  SUMMARY FUNCTION  #######
async def summary_and_cleanup(update, context, server_name):
    user_id = update.callback_query.from_user.id
    chat_id = update.callback_query.message.chat_id
    language = load_user_language(update.effective_user.id)
    differences = load_data(user_id, 'differences') or []
    full_name = update.callback_query.from_user.full_name
    username = update.callback_query.from_user.username
    user_url = f"https://t.me/{username}"

    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    if differences:
        max_difference = max(differences)
        total_difference = sum(differences)
        average_difference = round(total_difference / len(differences), 2) 

        if language == 'vi':
            summary_message = (
                f"<b>┏━━━━━━━━━━━━━━━💠━━━━━━━━━━━━━━━┓</b>\n"
                f"<b> 📊 THỐNG KÊ MÁY CHỦ: </b><code>{server_name}</code>\n"
                f"<b>┗━━━━━━━━━━━━━━━💠━━━━━━━━━━━━━━━┛</b>\n\n"
                f"🔹 <b>Tổng Requests:</b>  <code>{total_difference:,}</code>\n"
                f"🔸 <b>Cao Nhất Requests/s:</b> <code>{max_difference:,}</code>\n"
                f"🔹 <b>Trung Bình Requests/s:</b> <code>{round(average_difference):,}</code>\n\n"   
                f"🕒 <i>Thời gian:</i> <code>{now}</code>\n"
                f"👤 <i>Người dùng:</i> <a href='{user_url}'>🦄 {full_name}</a>\n\n"
        
                f"<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n"
                f"  ✨ <i>Dữ liệu được phân tích tự động</i> ✨\n"
                f"<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>"
            )
        else:
            summary_message = (
                "<code>"
                f"<b>┏━━━━━━━━━━━━━━━💠━━━━━━━━━━━━━━━┓</b>\n"
                f"<b> 📊 SERVER STATISTICS: </b><code>{server_name}</code>\n"
                f"<b>┗━━━━━━━━━━━━━━━💠━━━━━━━━━━━━━━━┛</b>\n\n"
                f"🔹 <b>Total Requests:</b>  <code>{total_difference:,}</code>\n"
                f"🔸 <b>Peak Requests/s:</b>  <code>{max_difference:,}</code>\n"
                f"🔹 <b>Avg Requests/s:</b>  <code>{round(average_difference):,}</code>\n\n"
                f"🕒 <i>Timestamp:</i> <code>{now}</code>\n"
                f"👤 <i>User:</i> <a href='{user_url}'>🦄 {full_name}</a>\n\n"
                
                f"<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>\n"
                f"  ✨ <i>Auto-analyzed statistics</i> ✨\n"
                f"<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>"
            )


        full_name = update.callback_query.from_user.full_name
        user_name = update.callback_query.from_user.username

        #group_message = await context.bot.send_message(chat_id=group_id, text=summary_message, parse_mode='HTML')
        #group_message_link = f"https://t.me/{group_message.chat.username}/{group_message.message_id}"      
        
        #save_user_performance(user_name, full_name, max_difference, total_difference, server_name,group_message_link)
        #save_user_performance_daily(user_name, full_name, max_difference, total_difference, server_name,group_message_link)
        
        #await context.bot.send_message(chat_id=chat_id,text=summary_message,parse_mode='HTML')
        
        #await send_log_to_user(context, chat_id, user_id, server_name, user_name)
        await send_graph_to_user(update, context, chat_id, user_id, server_name, summary_message)
        #await context.bot.send_message(chat_id=update.callback_query.message.chat_id, text=summary_message, parse_mode='HTML')
    else:
        await context.bot.send_message(chat_id=update.callback_query.message.chat_id, 
                                       text="Không có dữ liệu để hiển thị" if language == "vi" else "No data to display")


    os.remove(f"{user_id}_data.json")
    os.remove(f"{user_id}_logs.json")
    os.remove(f"{user_id}_graph.png")

def create_summary_message(language, server_name, total_received, max_received, average_received, total_packet, max_packet, average_packet, update):
    total_received_formatted = format_data_total(total_received)
    max_received_formatted = format_data_rate(max_received)
    average_received_formatted = format_data_rate(average_received)

    total_packet_formatted = format_number(total_packet)
    max_packet_formatted = format_number(max_packet)
    average_packet_formatted = format_number(int(average_packet))

    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    full_name = update.callback_query.from_user.full_name
    username = update.callback_query.from_user.username
    user_url = f"https://t.me/{username}"

    decorated_line = "╭───────────────────────────────╮\n"
    footer_line = "╰───────────────────────────────╯\n"

    if language == 'vi':
        return (
            "<code>"
            f"{decorated_line}"
            f"🖥️  THỐNG KÊ MÁY CHỦ: <b>{server_name}</b>\n"
            f"{footer_line}"
            f"📡 BĂNG THÔNG 📡\n"
            f"  ├─ 📊 Tổng cộng:      <b>{total_received_formatted}</b>\n"
            f"  ├─ 🚀 Cao nhất:       <b>{max_received_formatted}</b>\n"
            f"  └─ 🌈 Trung bình:     <b>{average_received_formatted}</b>\n"
            "───────────────────────────────\n"
            f"📦 GÓI TIN 📦\n"
            f"  ├─ 🔢 Tổng số:        <b>{total_packet_formatted}</b>\n"
            f"  ├─ ⚡ Cao nhất/s:     <b>{max_packet_formatted}</b>\n"
            f"  └─ 📥 Trung bình/s:   <b>{average_packet_formatted}</b>\n"
            "</code>\n"
            f"👤 Người yêu cầu: <a href='{user_url}'>🧑‍💻 {full_name}</a> • 🕒 {now}"
        )
    else:
        return (
            "<code>"
            f"{decorated_line}"
            f"🖥️  SERVER STATISTICS: <b>{server_name}</b>\n"
            f"{footer_line}"
            f"📡 BANDWIDTH 📡\n"
            f"  ├─ 📊 Total:         <b>{total_received_formatted}</b>\n"
            f"  ├─ 🚀 Peak:          <b>{max_received_formatted}</b>\n"
            f"  └─ 🌈 Average:       <b>{average_received_formatted}</b>\n"
            "───────────────────────────────\n"
            f"📦 PACKETS 📦\n"
            f"  ├─ 🔢 Total:         <b>{total_packet_formatted}</b>\n"
            f"  ├─ ⚡ Peak PPS:      <b>{max_packet_formatted}</b>\n"
            f"  └─ 📥 Avg PPS:       <b>{average_packet_formatted}</b>\n"
            "</code>\n"
            f"👤 Requested by: <a href='{user_url}'>🧑‍💻 {full_name}</a> • 🕒 {now}"
        )

async def summary_and_cleanup_l4(update, context, server_name):
    user_id = update.callback_query.from_user.id
    chat_id = update.callback_query.message.chat_id
    language = load_user_language(update.effective_user.id)

    try:
        with open(f"{user_id}_data_l4.json", 'r') as file:
            data = json.load(file)
            net_received = [entry['api_value'] for entry in data['net_received']]
            packet_received = [entry['packet_value'] for entry in data['net_received']]
    except (FileNotFoundError, KeyError):
        net_received = []
        packet_received = []

    if net_received and packet_received:
        max_received = max(net_received)
        total_received = sum(net_received)
        average_received = round(total_received / len(net_received), 2) if net_received else 0

        max_packet = max(packet_received)
        total_packet = sum(packet_received)
        average_packet = round(total_packet / len(packet_received), 2) if packet_received else 0

        summary_message = create_summary_message(language, server_name, total_received, max_received, average_received, total_packet, max_packet, average_packet, update)

        full_name = update.callback_query.from_user.full_name
        user_name = update.callback_query.from_user.username

        #group_message = await context.bot.send_message(chat_id=group_id, text=summary_message, parse_mode='HTML')
        #group_message_link = f"https://t.me/{group_message.chat.username}/{group_message.message_id}"

        #save_user_performance_l4(user_name, full_name, max_received, total_received, max_packet, total_packet, server_name, group_message_link)
        #save_user_performance_l4_daily(user_name, full_name, max_received, total_received, max_packet, total_packet, server_name, group_message_link)
        
        await send_graphl4_to_user(update, context, chat_id, user_id, server_name, summary_message)
        #await context.bot.send_message(chat_id=chat_id,text=summary_message,parse_mode='HTML')
    else:
        await context.bot.send_message(chat_id=chat_id, 
                                       text="Không có dữ liệu để hiển thị" if language == "vi" else "No data to display", 
                                       parse_mode='HTML')

    # Clean up files
    os.remove(f"{user_id}_data_l4.json")
    os.remove(f"{user_id}_graph_l4.png")




    os.remove(f"{user_id}_graph_l4.png")




