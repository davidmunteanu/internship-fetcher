import logging
import asyncio
import html
from telegram import Bot
from telegram.constants import ParseMode
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
from models import Job, Answer
from aggregators import to_tsv_row

logger = logging.getLogger(__name__)

bot = Bot(token=TELEGRAM_BOT_TOKEN) if TELEGRAM_BOT_TOKEN else None

def escape_md(text: str) -> str:
    # Telegram MarkdownV2 requires escaping these characters: _ * [ ] ( ) ~ > # + - = | { } . !
    escape_chars = r"_*[]()~>#+-=|{}.!"
    res = ""
    for c in str(text):
        if c in escape_chars:
            res += f"\\{c}"
        else:
            res += c
    return res

async def send_summary(n_new: int, n_companies: int, date_str: str) -> None:
    if not bot:
        logger.error("Telegram bot token not configured.")
        return
        
    text = (f"🔍 *Scan complete* \\— {escape_md(date_str)}\n"
            f"Found *{n_new}* new internships across {n_companies} companies")
            
    try:
        await bot.send_message(
            chat_id=TELEGRAM_CHAT_ID,
            text=text,
            parse_mode=ParseMode.MARKDOWN_V2,
            disable_web_page_preview=True,
        )
    except Exception as e:
        logger.error(f"Error sending Telegram summary: {e}")

async def send_job(job: Job, answers: list[Answer]) -> None:
    if not bot:
        return
        
    lines = [
        f"🏢 *{escape_md(job.company)}* \\— {escape_md(job.title)}",
        f"📍 {escape_md(job.location)}",
        f"🔗 [Apply here]({job.url})",
        "",
    ]

    if answers:
        lines.append("📝 *Application Q&A:*")
        lines.append("")
        for i, ans in enumerate(answers, 1):
            lines.append(f"*Q{i}:* {escape_md(ans.question_label)}")
            if ans.is_manual:
                lines.append(f"⚠️ _{escape_md(ans.suggested_answer)}_")
            else:
                lines.append(f"💡 {escape_md(ans.suggested_answer)}")
            lines.append("")
    else:
        lines.append("_No application questions available via API \\— check the link\\._")
        lines.append("")
        
    lines.append("───────────────")
    lines.append(f"_Found {escape_md(job.discovered_at)}_")

    text = "\n".join(lines)
    
    try:
        if len(text) > 4000:
            text = text[:4000] + "\n\\.\\.\\. message truncated"
            
        await bot.send_message(
            chat_id=TELEGRAM_CHAT_ID,
            text=text,
            parse_mode=ParseMode.MARKDOWN_V2,
            disable_web_page_preview=True,
        )
    except Exception as e:
        logger.error(f"Error sending Telegram job message for {job.id}: {e}")

# NEW: the Excel row as its own message, in a code block so one tap copies it
async def send_row(job: Job) -> None:
    if not bot:
        return
    try:
        await bot.send_message(
            chat_id=TELEGRAM_CHAT_ID,
            text=f"<pre>{html.escape(to_tsv_row(job))}</pre>",
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True,
        )
    except Exception as e:
        logger.error(f"Error sending Excel row for {job.id}: {e}")
