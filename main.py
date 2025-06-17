# main.py
import asyncio
import html
import time
from telegram import Bot
from config import API_KEY, CHAT_ID, HACKS_THREAD_ID, ONLINEHACKS_THREAD_ID
from scraper import get_all_hackathons
from state_manager import load_posted_links, save_posted_links

# A list of European countries to check against for location filtering
EUROPEAN_COUNTRIES = [
    "ireland", "serbia", "france", "ukraine", "uk", "croatia", "romania",
    "czech republic", "italy", "bulgaria", "germany", "spain", "portugal",
    "netherlands", "belgium", "switzerland", "austria", "greece", "sweden",
    "norway", "finland", "denmark", "poland", "hungary", "luxembourg"
]


async def main():
    """Main function to run the scraper and send notifications."""
    bot = Bot(token=API_KEY)
    posted_links = load_posted_links()

    print("Fetching hackathons from all sources...")
    all_hackathons = get_all_hackathons()

    # 1. Deduplicate hackathons based on their link
    unique_hackathons = []
    seen_links = set()
    for hackathon in all_hackathons:
        link = hackathon.get('link')
        if link and link not in seen_links:
            unique_hackathons.append(hackathon)
            seen_links.add(link)

    # 2. Filter for relevant hackathons (Online or in Europe)
    relevant_hackathons = [
        h for h in unique_hackathons
        if 'online' in h.get('location', '').lower() or
           any(country in h.get('location', '').lower() for country in EUROPEAN_COUNTRIES)
    ]

    # 3. Identify which of the relevant hackathons are new
    new_hackathons = [
        h for h in relevant_hackathons if h.get('link') and h['link'] not in posted_links
    ]

    if not new_hackathons:
        print("No new hackathons found to post.")
        return

    print(f"Found {len(new_hackathons)} new hackathons. Sending notifications...")

    # 4. Loop through each new hackathon and send a single message
    for hackathon in new_hackathons:
        # Clean the title to remove HTML entities like &amp;
        clean_title = html.unescape(hackathon.get('title', 'N/A'))
        link = hackathon.get('link', '#')
        source = hackathon.get('source', 'Unknown Source')

        # Build a detailed message for this specific hackathon
        message_text = f"📢 **{clean_title}**\n\n"

        details = []
        if hackathon.get('location'):
            details.append(f"📍 **Location:** {hackathon['location']}")
        if hackathon.get('mode'):
            details.append(f"💻 **Mode:** {hackathon['mode']}")

        # Handle date formatting gracefully
        if hackathon.get('startDate'):
            if hackathon.get('endDate'):
                details.append(f"🗓️ **Dates:** {hackathon['startDate']} - {hackathon['endDate']}")
            else:
                details.append(f"🗓️ **Dates:** {hackathon['startDate']}")

        if details:
            message_text += "\n".join(details)

        message_text += f"\n\n🔗 [Event Link]({link})\n*Source: {source}*"
        is_online = 'online' in hackathon.get('location', '').lower() or \
                    'online' in hackathon.get('mode', '').lower()

        if is_online:
            target_thread_id = ONLINEHACKS_THREAD_ID
        else:
            target_thread_id = HACKS_THREAD_ID

        try:
            # Send the message to the dynamically chosen topic in your Telegram group
            await bot.send_message(
                chat_id=CHAT_ID,
                text=message_text,
                message_thread_id=target_thread_id,
                parse_mode='Markdown',
                disable_web_page_preview=True
            )

            print(f"Successfully sent message for: {clean_title}")

            # Add the link to our set of posted links immediately after sending
            posted_links.add(link)

        except Exception as e:
            print(f"Failed to send message for {clean_title}: {e}")

        await asyncio.sleep(2)

    # Save the updated set of posted links to the file
    save_posted_links(posted_links)
    print("All new hackathons have been posted.")


if __name__ == '__main__':
    asyncio.run(main())
