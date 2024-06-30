import ftfy
import re
import time
from datetime import datetime

def parse_txt_to_dict(filepath):
    # pattern to extract date, time, sender, and message
    pattern = r"\[(\d{1,2}/\d{1,2}/\d{4}), (\d{2}:\d{2}:\d{2})\] (.+?): (.+)"
    messages = []

    with open(filepath, 'r', encoding='utf-8') as file:
        for line in file:
            match = re.match(pattern, line.strip())
            if match:
                date_str, time_str, sender, message = match.groups()
                
                dt = datetime.strptime(f"{date_str} {time_str}", "%d/%m/%Y %H:%M:%S")
                timestamp_ms = int(time.mktime(dt.timetuple()) * 1000)
                
                message_dict = {
                    "sender_name": sender,
                    "timestamp_ms": timestamp_ms,
                    "content": message,
                }
                messages.append(message_dict)
    
    return {"messages": messages}

def include_message(msg):
    omit_phrases = {
        "Liked a message",
        "You called a contact.",
        "sent an attachment.",
        "You missed a video call with",
        "You missed a call from",
        "You named the group",
        "Messages and calls are end-to-end encrypted.",
        "changed their phone number.",
        "image omitted",
        "video omitted",
        "audio omitted",
        "GIF omitted",
        "sticker omitted",
        "Missed voice call",
        "Missed video call",
    }

    content = ftfy.fix_text(msg.get("content", "").replace('\\', '').replace('"', "'").replace("\r", ""))
    
    if any(phrase in content for phrase in omit_phrases):
        return False

    if "Reacted" in content and "to your message" in content:
        return False

    if not content.strip():
        return False

    return True
def format_message(msg):
    content = ftfy.fix_text(msg.get("content", "").replace('\\', '').replace('"', "'").replace("\r", ""))

    if msg.get("share", {}).get("link", ""):
        if not content.strip():
            content = msg.get("share", {}).get("link", "")
        else:
            content += "\n\n" + msg.get("share", {}).get("link", "")
    
    if content == "You sent an attachment.":
        content = msg.get("share", {}).get("link", "")
    if content.strip():
        return f"{msg['sender_name']}: {content}"
    else:
        return ""