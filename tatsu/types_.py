"""
tatsu.types_
------------

Typings/data structures for the Tatsu API.
"""

import datetime

from msgspec import Struct

from .enums import CurrencyType, SubscriptionType

__all__ = (
    "GuildMemberPoints",
    "GuildMemberScore",
    "GuildMemberRanking",
    "Ranking",
    "GuildRankings",
    "User",
    "StorePrice",
    "StoreListing",
)


class GuildMemberPoints(Struct):
    """A Discord guild member's points information.

    Parameters
    ----------
    guild_id : :class:`str`
        The Discord ID of the guild.
    points : :class:`int`
        The user's points.
    rank : :class:`int`
        The user's rank based on their points.
    user_id : :class:`str`
        The user's Discord ID.
    """

    guild_id: str
    points: int
    rank: int
    user_id: str


class GuildMemberScore(Struct):
    """A Discord guild member's score information.

    Parameters
    ----------
    guild_id : :class:`str`
        The Discord ID of the guild.
    score : :class:`int`
        The user's score.
    user_id : :class:`str`
        The user's Discord ID.
    """

    guild_id: str
    score: int
    user_id: str


class GuildMemberRanking(Struct):
    """A Discord guild member's ranking information over some period of time.

    Attributes
    ----------
    guild_id : :class:`str`
        The Discord ID of the guild.
    rank : :class:`int`
        The user's rank.
    score : :class:`int`
        The user's score.
    user_id : :class:`str`
        The user's Discord ID.
    """

    guild_id: str
    rank: int
    score: int
    user_id: str


class Ranking(Struct):
    """A generic rank information object.

    Attributes
    ----------
    rank : :class:`int`
        The user's rank.
    score : :class:`int`
        The user's score.
    user_id : :class:`str`
        The user's Discord ID.
    """

    rank: int
    score: int
    user_id: str


class GuildRankings(Struct):
    """All the rankings in a guild over some period of time.

    Attributes
    ----------
    guild_id : :class:`str`
        The Discord ID of the guild.
    rankings : list[:class:`Ranking`]
        The rankings.
    """

    guild_id: str
    rankings: list[Ranking] = []


class User(Struct):
    """A Tatsu-bot user.

    Attributes
    ----------
    avatar_hash : class:`str`
        The user's Discord avatar hash.
    avatar_url : class:`str`
        The user's Discord avatar URL.
    credits : :class:`int`
        The amount of credits the user has.
    discriminator : class:`str`
        The user's 4 digit discriminator.
    id : class:`str`
        The user's Discord ID.
    info_box : class:`str`
        The text in the user's info box.
    reputation : :class:`int`
        The number of reputation points the user has.
    subscription_type : :class:`int`
        The user's subscription type.
    subscription_renewal : :class:`str`, optional
        The subscription renewal time if the user has a subscription. Optional
    title : class:`str`
        The text in the user's title.
    tokens : :class:`int`
        The amount of tokens the user has.
    username : class:`str`
        The user's Discord username.
    xp : :class:`int`
        The number of experience points the user has.
    """

    avatar_hash: str
    avatar_url: str
    credits: int
    discriminator: str
    id: str
    info_box: str
    reputation: int
    subscription_type: SubscriptionType
    title: str
    tokens: int
    username: str
    xp: int
    subscription_renewal: datetime.datetime | None = None


class StorePrice(Struct):
    """A price of a Tatsu store item.

    Attributes
    ----------
    currency : :class:`CurrencyType`
        The currency type.
    amount : :class:`float`
        The cost of the item in the currency.
    """

    currency: CurrencyType
    amount: float


class StoreListing(Struct):
    """The listing of a Tatsu store item.

    Attributes
    ----------
    id : :class:`str`
        The ID of the store listing.
    name : :class:`str
        The name of the item.
    summary : :class:`str
        The summary of the item.
    description : :class:`str
        The description of the item.
    new : :class:`str
        Whether this is a new item in the store.
    preview : :class:`str`, optional
        The URL to an image preview of the item. Optional.
    prices : list[:class:`StorePrice`], optional
        The prices for the item. Optional.
    categories : list[: :class:`str`], optional
        The categories for the item. Optional
    tags : list[: :class:`str`], optional
        The tags for the item. Optional.
    """

    id: str
    name: str
    summary: str
    description: str
    new: bool
    preview: str | None = None
    prices: list[StorePrice] = []
    categories: list[str] = []
    tags: list[str] = []
