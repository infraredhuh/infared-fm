from PIL import Image
from typing import List, Literal, Optional, Union, TYPE_CHECKING
from io import BytesIO
import math

if TYPE_CHECKING:
    from . import LastFMClient

OutputMode = Literal["image", "file", "bytes"]
ImageType = Literal["albums", "artists", "tracks"]
ImageFormat = Literal["JPEG", "PNG"]
TimePeriod = Literal["overall", "7day", "1month", "3month", "6month", "12month"]


class ChartBuilder:
    def __init__(
        self,
        *,
        client: "LastFMClient",
        output_mode: OutputMode = "image",
        image_format: ImageFormat = "JPEG",
        background_color: str = "black"
    ):
        self.client = client
        self.output_mode = output_mode
        self.image_format = image_format
        self.background_color = background_color
        self._fallback_image = Image.new("RGB", (300, 300), color="#222222")

    async def _fetch_image(self, url: Optional[str]) -> Image.Image:
        if not url:
            return self._fallback_image.copy()
        try:
            async with self.client.session.get(url) as resp:
                if resp.status != 200:
                    return self._fallback_image.copy()
                data = await resp.read()
                return Image.open(BytesIO(data)).convert("RGB")
        except Exception:
            return self._fallback_image.copy()

    async def _search_itunes_art(self, query: str) -> Optional[str]:
        url = "https://itunes.apple.com/search"
        params = {
            "term": query,
            "media": "music",
            "limit": 1,
        }
        try:
            async with self.client.session.get(url, params=params) as resp:
                if resp.status != 200:
                    return None
                data = await resp.json()
                results = data.get("results")
                if not results:
                    return None
                return results[0].get("artworkUrl100", "").replace("100x100", "512x512")
        except Exception:
            return None

    async def _get_image_urls(
        self,
        type: ImageType,
        username: str,
        limit: int,
        period: TimePeriod
    ) -> List[str]:
        urls = []

        if type == "albums":
            data = await self.client.user.get_top_albums(user=username, limit=limit, period=period)
            for album in data:
                images = album.raw.get("image", [])
                url = next((img["#text"] for img in reversed(images) if img.get("#text")), None)

                if not url:
                    query = f"{album.artist} - {album.name}" if album.artist else album.name
                    url = await self._search_itunes_art(query)

                urls.append(url or "")

        elif type == "artists":
            data = await self.client.user.get_top_artists(user=username, limit=limit, period=period)
            for artist in data:
                images = artist.raw.get("image", [])
                url = next((img["#text"] for img in reversed(images) if img.get("#text")), None)

                if not url:
                    url = await self._search_itunes_art(artist.name)

                urls.append(url or "")

        elif type == "tracks":
            data = await self.client.user.get_top_tracks(user=username, limit=limit, period=period)
            for track in data:
                images = track.raw.get("image", [])
                url = next((img["#text"] for img in reversed(images) if img.get("#text")), None)

                if not url:
                    query = f"{track.artist} - {track.name}" if track.artist else track.name
                    url = await self._search_itunes_art(query)

                urls.append(url or "")

        return urls

    async def build_collage(
        self,
        username: str,
        type: ImageType = "albums",
        period: TimePeriod = "overall",
        limit: int = 25,
        grid_size: Optional[int] = None,
        image_size: int = 300,
        output_path: Optional[str] = None
    ) -> Union[Image.Image, bytes, None]:
        urls = await self._get_image_urls(type, username, limit, period)

        count = min(len(urls), limit)
        grid = grid_size or math.isqrt(count)
        total_slots = grid * grid
        urls = (urls + [""] * total_slots)[:total_slots]  # pad 

        images = []
        for url in urls:
            img = await self._fetch_image(url)
            img = img.resize((image_size, image_size))
            images.append(img)

        collage = Image.new(
            "RGB",
            (grid * image_size, grid * image_size),
            color=self.background_color
        )

        for idx, img in enumerate(images):
            row = idx // grid
            col = idx % grid
            collage.paste(img, (col * image_size, row * image_size))

        if self.output_mode == "file":
            if not output_path:
                raise ValueError("output_path is required when output_mode='file'")
            collage.save(output_path, format=self.image_format)
            return None

        elif self.output_mode == "bytes":
            buffer = BytesIO()
            collage.save(buffer, format=self.image_format)
            buffer.seek(0)
            return buffer.read()

        elif self.output_mode == "image":
            return collage

        else:
            raise ValueError(f"Invalid output_mode: {self.output_mode}")

