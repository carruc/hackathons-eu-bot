# main.py
import asyncio
import time
from telegram import Bot
from config import API_KEY, CHAT_ID, HACKS_THREAD_ID
# ... (imports and config remain the same) ...
from scraper import get_all_hackathons  # Import the new function
from state_manager import load_posted_links, save_posted_links


async def main():
    bot = Bot(token=API_KEY)
    posted_links = load_posted_links()

    print("Fetching new hackathons from all sources...")
    all_hackathons = get_all_hackathons()  # One function to get everything

    new_hackathons = [
        h for h in all_hackathons if h['link'] not in posted_links
    ]

    if not new_hackathons:
        print("No new hackathons found.")
        return

    print(f"Found {len(new_hackathons)} new hackathons. Sending notifications...")

    for hackathon in new_hackathons:
        message_text = (
            f"📢 **{hackathon['title']}**\n\n"
            f"Source: *{hackathon['source']}*\n"
            f"Link: {hackathon['link']}"
        )

        await bot.send_message(
            chat_id=CHAT_ID,
            text=message_text,
            message_thread_id=HACKS_THREAD_ID,
            parse_mode='Markdown',
            disable_web_page_preview=True
        )

        posted_links.add(hackathon['link'])
        await asyncio.sleep(1)

    save_posted_links(posted_links)
    print("Notifications sent and state saved.")


if __name__ == '__main__':
    # asyncio.run(main())
    print(get_all_hackathons())
