import random
from dataclasses import dataclass
from enum import Enum
from functools import total_ordering
from typing import Optional


class Suit(Enum):
    DIAMOND = 0
    HEART = 1
    SPADE = 2
    CLUB = 3

    def __str__(self):
        return self.name.capitalize()

    def __repr__(self):
        return self.__str__()

    @classmethod
    def from_string(cls, string):
        string = string.lower()
        if "diamond" in string or "♦" in string:
            return Suit.DIAMOND
        elif "heart" in string or "♥" in string:
            return Suit.HEART
        elif "spade" in string or "♠" in string:
            return Suit.SPADE
        elif "club" in string or "♣" in string:
            return Suit.CLUB
        raise ValueError

    @classmethod
    def fail_suits(cls):
        return {Suit.HEART, Suit.SPADE, Suit.CLUB}

    @classmethod
    def trump_suit(cls):
        return {Suit.DIAMOND}

    @property
    def symbol(self):
        match self.name:
            case "DIAMOND":
                return "\u0332♦"
            case "HEART":
                return "♥"
            case "SPADE":
                return "♠"
            case "CLUB":
                return "♣"
        raise NotImplementedError


@total_ordering
class Power(Enum):
    SEVEN = 0
    EIGHT = 1
    NINE = 2
    KING = 3
    TEN = 5
    ACE = 8
    JACK = 13
    QUEEN = 21

    def __str__(self):
        return self.name.capitalize()

    def __repr__(self):
        return self.__str__()

    def __lt__(self, other):
        if self.__class__ is other.__class__:
            return self.value < other.value
        raise NotImplementedError

    @classmethod
    def from_string(cls, string):
        string = string.lower()
        if "seven" in string or "7" in string:
            return Power.SEVEN
        elif "eight" in string or "8" in string:
            return Power.EIGHT
        elif "nine" in string or "9" in string:
            return Power.NINE
        elif "ten" in string or "10" in string:
            return Power.TEN
        elif "jack" in string or "j" in string:
            return Power.JACK
        elif "ace" in string or "a" in string.lstrip()[:1]:
            return Power.ACE
        elif "king" in string or "k" in string:
            return Power.KING
        elif "queen" in string or "q" in string:
            return Power.QUEEN
        raise ValueError

    @property
    def symbol(self):
        match self.name:
            case "SEVEN":
                return "7"
            case "EIGHT":
                return "8"
            case "NINE":
                return "9"
            case "TEN":
                return "10"
            case "KING":
                return "K"
            case "ACE":
                return "A"
            case "JACK":
                return "\u0332J"
            case "QUEEN":
                return "\u0332Q"
        raise NotImplementedError


# strength for trump cards
#     SEVEN = 21
#     EIGHT = 22
#     NINE = 23
#     KING = 24
#     TEN = 26
#     ACE = 29
#     JACK = 34
#     QUEEN = 42


_STRENGTH_POWER_OFFSET = max([e.value for e in Power])


@dataclass(frozen=True, slots=True)
@total_ordering
class Card:
    """
    Every card is either trump or fail.
    All diamonds, jacks, and queens are trump.
    All other cards are fail.

    Every card, whether trump or fail, has a point value.
    Numbered cards 7, 8, and 9 are worth 0.
    The numbered card 10 is worth 10 points.
    All jacks are worth 2 points.
    All Kings are worth 4 points.
    All Queens are worth 3 points.
    """

    _suit: Suit
    power: Power
    _mask: Optional[Suit] = None

    def __str__(self):
        power_str = "?" if self.is_hidden else self.power.symbol
        return f"{power_str}{self.suit.symbol}"

    def __repr__(self):
        return self.__str__()

    def __lt__(self, other):
        # Does it make sense for a Card class to implement comparisons?
        # Does it make sense for you to shut up about it ????
        if self.__class__ is other.__class__:
            return self.strength < other.strength
        raise NotImplementedError

    @classmethod
    def from_string(cls, string: str):
        """
        Creates an instance of Card from a string such as 'Ace of Spades' or 'Seven of Clubs'
        Does not support under/ hidden/ masked cards
        """

        suit = Suit.from_string(string)
        power = Power.from_string(string)
        return cls(suit, power)

    @property
    def reveal(self):
        if self.is_hidden:
            return Card(self._suit, self.power)
        return self

    @property
    def suit(self):
        return self._mask if self._mask else self._suit

    @property
    def is_hidden(self):
        return self._mask is not None

    @property
    def is_trump(self):
        return not self.is_hidden and (
            self.suit == Suit.DIAMOND or self.power >= Power.JACK
        )

    @property
    def is_fail(self):
        return not self.is_trump

    @property
    def strength(self):
        """
        Power adjusted for trump
        """
        if self.is_trump:
            return self.power.value + _STRENGTH_POWER_OFFSET
        elif self.is_hidden:
            return -1
        else:
            return self.power.value

    @property
    def points(self):
        if self.is_hidden or self.power < Power.KING:
            return 0
        elif self.power == Power.KING:
            return 4
        elif self.power == Power.TEN:
            return 10
        elif self.power == Power.ACE:
            return 11
        elif self.power == Power.JACK:
            return 2
        elif self.power == Power.QUEEN:
            return 3
        raise RuntimeError("Not Implemented")


SEVEN_OF_DIAMONDS = Card(Suit.DIAMOND, Power.SEVEN)
EIGHT_OF_DIAMONDS = Card(Suit.DIAMOND, Power.EIGHT)
NINE_OF_DIAMONDS = Card(Suit.DIAMOND, Power.NINE)
KING_OF_DIAMONDS = Card(Suit.DIAMOND, Power.KING)
TEN_OF_DIAMONDS = Card(Suit.DIAMOND, Power.TEN)
ACE_OF_DIAMONDS = Card(Suit.DIAMOND, Power.ACE)
JACK_OF_DIAMONDS = Card(Suit.DIAMOND, Power.JACK)
QUEEN_OF_DIAMONDS = Card(Suit.DIAMOND, Power.QUEEN)

SEVEN_OF_HEARTS = Card(Suit.HEART, Power.SEVEN)
EIGHT_OF_HEARTS = Card(Suit.HEART, Power.EIGHT)
NINE_OF_HEARTS = Card(Suit.HEART, Power.NINE)
KING_OF_HEARTS = Card(Suit.HEART, Power.KING)
TEN_OF_HEARTS = Card(Suit.HEART, Power.TEN)
ACE_OF_HEARTS = Card(Suit.HEART, Power.ACE)
JACK_OF_HEARTS = Card(Suit.HEART, Power.JACK)
QUEEN_OF_HEARTS = Card(Suit.HEART, Power.QUEEN)

SEVEN_OF_SPADES = Card(Suit.SPADE, Power.SEVEN)
EIGHT_OF_SPADES = Card(Suit.SPADE, Power.EIGHT)
NINE_OF_SPADES = Card(Suit.SPADE, Power.NINE)
KING_OF_SPADES = Card(Suit.SPADE, Power.KING)
TEN_OF_SPADES = Card(Suit.SPADE, Power.TEN)
ACE_OF_SPADES = Card(Suit.SPADE, Power.ACE)
JACK_OF_SPADES = Card(Suit.SPADE, Power.JACK)
QUEEN_OF_SPADES = Card(Suit.SPADE, Power.QUEEN)

SEVEN_OF_CLUBS = Card(Suit.CLUB, Power.SEVEN)
EIGHT_OF_CLUBS = Card(Suit.CLUB, Power.EIGHT)
NINE_OF_CLUBS = Card(Suit.CLUB, Power.NINE)
KING_OF_CLUBS = Card(Suit.CLUB, Power.KING)
TEN_OF_CLUBS = Card(Suit.CLUB, Power.TEN)
ACE_OF_CLUBS = Card(Suit.CLUB, Power.ACE)
JACK_OF_CLUBS = Card(Suit.CLUB, Power.JACK)
QUEEN_OF_CLUBS = Card(Suit.CLUB, Power.QUEEN)


def create_piquet_pack():
    cards = [
        SEVEN_OF_DIAMONDS,
        EIGHT_OF_DIAMONDS,
        NINE_OF_DIAMONDS,
        KING_OF_DIAMONDS,
        TEN_OF_DIAMONDS,
        ACE_OF_DIAMONDS,
        JACK_OF_DIAMONDS,
        QUEEN_OF_DIAMONDS,
        SEVEN_OF_HEARTS,
        EIGHT_OF_HEARTS,
        NINE_OF_HEARTS,
        KING_OF_HEARTS,
        TEN_OF_HEARTS,
        ACE_OF_HEARTS,
        JACK_OF_HEARTS,
        QUEEN_OF_HEARTS,
        SEVEN_OF_SPADES,
        EIGHT_OF_SPADES,
        NINE_OF_SPADES,
        KING_OF_SPADES,
        TEN_OF_SPADES,
        ACE_OF_SPADES,
        JACK_OF_SPADES,
        QUEEN_OF_SPADES,
        SEVEN_OF_CLUBS,
        EIGHT_OF_CLUBS,
        NINE_OF_CLUBS,
        KING_OF_CLUBS,
        TEN_OF_CLUBS,
        ACE_OF_CLUBS,
        JACK_OF_CLUBS,
        QUEEN_OF_CLUBS,
    ]
    assert len(cards) == 32 == len(set(cards))
    assert sum(c.points for c in cards) == 120
    assert not any(c.is_hidden for c in cards)

    random.shuffle(cards)
    return cards
