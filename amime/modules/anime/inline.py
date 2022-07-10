import asyncio
import re
from typing import List

import anilist
from pyrogram import filters
from pyrogram.errors import QueryIdInvalid
from pyrogram.types import InlineQuery, InlineQueryResultPhoto
from pyromod.helpers import ikb

from amime.amime import Amime
from amime.database import Episodes

@Amime.on_inline_query(filters.regex(r"^!a (?P<query>.+)"))
async def anime_inline(bot: Amime, inline_query: InlineQuery):
    query = inline_query.matches[0]["query"].strip()
    lang = inline_query._lang
    user = inline_query.from_user

    is_collaborator = await filters.sudo(bot, inline_query) or await filters.collaborator(bot, inline_query)


    if query.startswith("!"):
        inline_query.continue_propagation()

    results: List[InlineQueryResultPhoto] = []

    async with anilist.AsyncClient() as client:
        search_results = await client.search(query, "anime", 20)
        while search_results is None:
            search_results = await client.search(query, "anime", 10)
            await asyncio.sleep(0.5)

        for result in search_results:
            anime = await client.get(result.id, "anime")

            if anime is None:
                continue

            episodes = await Episodes.filter(anime=anime.id)
            episodes = sorted(episodes, key=lambda episode: episode.number)
            episodes = [*filter(lambda episode: len(episode.file_id) > 0, episodes)]
          

            photo = f"https://img.anili.st/media/{anime.id}"


            #
            
            
            
            if len(episodes) > 0 and hasattr(anime, "genres"):
                description = f"✅ Tersedia | {anime.episodes}Eps ({anime.format})"
                description += f"\nGenre: {', '.join(anime.genres)}"

            if len(episodes) < 1 and hasattr(anime, "genres"):
                description = f"❌ Tidak Ada | {anime.episodes}Eps ({anime.format})"    
                description += f"\nGenre: {', '.join(anime.genres)}"        

            text = f"<b>{anime.title.romaji}</b>"
            text += f"\n<b>ID</b>: <code>{anime.id}</code> (<b>ANIME</b>)"

            keyboard = [
                [
                    (
                        lang.view_more_button,
                        f"https://t.me/{bot.me.username}/?start=anime_{anime.id}",
                        "url",
                    ),
                    (lang.search_button, "!a ", "switch_inline_query_current_chat"),

                ],
            ]

            results.append(
                InlineQueryResultPhoto(
                    photo_url=photo,
                    title=f"{anime.title.romaji}",
                    description=description,
                    caption=text,
                    reply_markup=ikb(keyboard),
                )
            )

    if is_collaborator and len(results) > 0:
        try:
            await inline_query.answer(
                results=results,
                is_gallery=False,
                cache_time=0,
            )
        except QueryIdInvalid:
            pass

