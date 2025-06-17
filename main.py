# main.py
import asyncio
import html
from telegram import Bot
from config import API_KEY, CHAT_ID, HACKS_THREAD_ID
from scraper import get_all_hackathons
from state_manager import load_posted_links, save_posted_links


async def main():
    bot = Bot(token=API_KEY)
    posted_links = load_posted_links()

    print("Fetching new hackathons from all sources...")
    all_hackathons = get_all_hackathons()  # One function to get everything

    unique_hackathons = []
    seen_links = set()

    for hackathon in all_hackathons:
        link = hackathon.get('link')
        if link and link not in seen_links:
            unique_hackathons.append(hackathon)
            seen_links.add(link)

    european_countries = [
        "ireland", "serbia", "france", "ukraine", "uk", "croatia",
        "czech republic", "italy", "bulgaria", "germany", "spain",
        "portugal", "netherlands", "belgium", "switzerland", "austria",
        "greece", "sweden", "norway", "finland", "denmark", "poland"
    ]

    european_hackathons = [
        h for h in unique_hackathons
        if 'online' in h.get('location', '').lower() or
           any(country in h.get('location', '').lower() for country in european_countries)
    ]

    new_hackathons = [
        h for h in european_hackathons if h['link'] not in posted_links
    ]

    if not new_hackathons:
        print("No new hackathons found.")
        return

    print(f"Found {len(new_hackathons)} new hackathons. Sending notifications...")

    for hackathon in new_hackathons:
        clean_title = html.unescape(hackathon.get('title', 'N/A'))

        message_text = (
            f"📢 **{clean_title}**\n"
            f"{hackathon['startDate']} @ {hackathon['location']}\n"
            f"More info: {hackathon['link']}\n\n"
            f"Source: {hackathon['source']}\n"
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
    asyncio.run(main())