# -*- coding: utf-8 -*-
import httpx
import json
from datetime import datetime
from zoneinfo import ZoneInfo
import asyncio

async def get_github_releases():
    url = f"https://api.github.com/repos/devsetgo/bumpcalver/releases?per_page=1000"
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        response.raise_for_status()  # Raise an exception if the request was unsuccessful
    return response.json()

def set_date_time(published_at):
    published_at = datetime.strptime(published_at, "%Y-%m-%dT%H:%M:%SZ")
    published_at = published_at.replace(tzinfo=ZoneInfo("UTC"))  # Make it aware in UTC
    published_at = published_at.astimezone(ZoneInfo("America/New_York"))  # Convert to US Eastern Time
    return published_at.strftime("%Y %B %d, %H:%M")  # Format it to a more human-readable format

async def main():
    try:
        releases = await get_github_releases()  # Fetch releases from a GitHub repository
    except httpx.HTTPStatusError as e:
        print(f"HTTP error occurred: {e}")
        return
    except Exception as e:
        print(f"An error occurred: {e}")
        return

    try:
        with open("CHANGELOG.md", "r") as f:
            lines = f.readlines()
    except FileNotFoundError:
        print("CHANGELOG.md not found.")
        return

    try:
        index = lines.index("## Latest Changes\n") + 1
    except ValueError:
        print("## Latest Changes not found in CHANGELOG.md.")
        return

    lines = lines[:index]  # Slice the list of lines at the index of "## Latest Changes"

    for release in releases:
        try:
            name = release["name"]
            tag_name = release["tag_name"]
            published_at = set_date_time(release["published_at"])
            body = release["body"]
            release_url = release["html_url"]
        except KeyError as e:
            print(f"Key error: {e}")
            continue

        markdown = f"### <span style='color:blue'>{name}</span> ([{tag_name}]({release_url}))\n\n{body}\n\nPublished Date: {published_at}\n\n"
        lines.append(markdown)

    try:
        with open("CHANGELOG.md", "w") as f:
            f.writelines(lines)
    except Exception as e:
        print(f"An error occurred while writing to CHANGELOG.md: {e}")

if __name__ == "__main__":
    asyncio.run(main())
