from copy import deepcopy
from enum import Enum
from typing import Optional

from src.deck import Card


class PickStyle(Enum):
    CALLED_ACE = 0
    ALONE = 1
    UNDER = 2
    CALLED_TEN = 3

    def __str__(self):
        return self.name.capitalize().replace("_", " ")

    def __repr__(self):
        return self.name


class Trick:
    """
    A readonly ordered set of cards with a maximum length of 5
    """

    __slots__ = ["_cards", "_is_frozen"]

    def __init__(self, cards: list[Card] = None):
        """
        :raises ValueError: If this trick already contains the given card or the maximum of 5 cards
        """
        if cards is None:
            cards = []
        if len(cards) > 5:
            raise ValueError(
                f"Maximum number of cards is 5 but {len(cards)} were given"
            )
        if len(set(cards)) != len(cards):
            raise ValueError(f"Trick cannot contain duplicate cards")
        self._cards = cards
        self._is_frozen = False

    def __setattr__(self, key, value):
        if getattr(self, "_is_frozen", False):
            raise AttributeError
        object.__setattr__(self, key, value)

    def __iter__(self):
        return iter(self._cards)

    def __getitem__(self, i):
        return self._cards[i]

    def __len__(self):
        return len(self._cards)

    def __contains__(self, card: Card):
        return card in self._cards

    def play(self, card):
        """
        :returns: A new Trick with the card appended
        :raises ValueError: If this trick already contains the given card or the maximum of 5 cards
        """
        return type(self)(self._cards + [card])

    def index(self, card: Card):
        """
        :raises ValueError: if the value is not present
        """
        return self._cards.index(card)

    @property
    def points(self) -> int:
        return sum([c.points for c in self._cards])

    @property
    def is_full(self):
        return len(self._cards) == 5


class Hand:
    """
    A readonly ordered set of tricks with a maximum length of 6
    """

    __slots__ = [
        "dealer_seat",
        "picker_seat",
        "pick_style",
        "called_card",
        "_tricks",
        "_is_frozen",
    ]

    def __init__(
        self,
        dealer_seat: int,
        picker_seat: int,
        pick_style: PickStyle,
        called_card: Card = None,
        tricks: list[Trick] = None,
    ):
        """
        :raises ValueError: If the length of tricks is more than 6 or an invalid combination of PickStyle and called
        card is used.
        """
        self.dealer_seat = dealer_seat
        self.picker_seat = picker_seat

        if (called_card is None and pick_style != PickStyle.ALONE) or (
            called_card is not None and pick_style == PickStyle.ALONE
        ):
            raise ValueError(
                f"PickerStyle {pick_style} incompatible with called card {called_card}"
            )
        self.pick_style = pick_style
        self.called_card = called_card

        if tricks is None:
            tricks = []
        elif len(tricks) > 6:
            raise ValueError(
                f"Maximum number of tricks is 6 but {len(tricks)} were given"
            )
        self._tricks = tricks
        self._is_frozen = True

    def __setattr__(self, key, value):
        if getattr(self, "_is_frozen", False):
            raise AttributeError
        object.__setattr__(self, key, value)

    def __iter__(self):
        return iter(self._tricks)

    def __getitem__(self, i):
        return self._tricks[i]

    def __len__(self):
        return len(self._tricks)

    def play(self, card: Card):
        """
        :returns: A new instance of Hand with the card appended
        :raises ValueError: If the length of tricks is more than 6 or the combo of PickStyle and called card is invalid
        """
        tricks = deepcopy(self._tricks)
        trick = []
        try:
            tricks[-1] = self._tricks[-1].play(card)
        except (IndexError, ValueError):
            trick.append(Trick([card]))

        return type(self)(
            self.dealer_seat,
            self.picker_seat,
            self.pick_style,
            self.called_card,
            tricks + trick,
        )


def winning_card_idx(trick: Trick, called_card: Optional[Card] = None) -> int:
    """
    :returns: index of the winning card
    :raises ValueError: if the trick is empty
    """
    if any(c.is_trump for c in trick):
        return trick.index(max([c for c in trick if c.is_trump], key=lambda c: c.power))

    if called_card in trick and trick[0].suit == called_card.suit:
        return trick.index(called_card)

    lead_suit = trick[0].suit
    return trick.index(
        max(
            [c for c in trick if c.is_fail and c.suit == lead_suit],
            key=lambda c: c.power,
        )
    )


def winning_card(trick: Trick, called_card: Optional[Card]):
    """
    :returns: the winning card
    :raises ValueError: if the trick is empty
    """
    return trick[winning_card_idx(trick, called_card)]


def tricks_taken_by_seat(hand: Hand, *seats: int) -> list[Trick]:
    taken_tricks = []
    lead_seat = (hand.dealer_seat + 1) % 5
    for trick in hand:
        winning_idx = winning_card_idx(trick, hand.called_card)
        winner_seat = (winning_idx + lead_seat) % 5

        if winner_seat in seats:
            taken_tricks.append(trick)

        # winner always leads the next trick
        lead_seat = winner_seat

    return taken_tricks


def cards_played_by_seat(hand: Hand, *seats: int) -> list[Card]:
    assert all(0 <= seat <= 4 for seat in seats)
    cards = []
    lead_seat = (hand.dealer_seat + 1) % 5
    for trick in hand:
        for seat in seats:
            seat_idx = (lead_seat + seat) % 5
            cards.append(trick[seat_idx])

        winning_idx = winning_card_idx(trick, hand.called_card)
        winner_seat = (winning_idx + lead_seat) % 5

        # winner always leads the next trick
        lead_seat = winner_seat

    return cards


def points_taken_by_seat(*seats: int) -> int:
    return sum(
        [card.points for trick in tricks_taken_by_seat(*seats) for card in trick]
    )


def seat_with_card(hand: Hand, card: Card) -> int:
    """
    :returns: The seat that played the given card
    :raises ValueError: If the card does not exist in any of the tricks
    """
    lead_seat = (hand.dealer_seat + 1) % 5
    for trick in hand:
        winning_idx = winning_card_idx(trick, hand.called_card)
        winner_seat = (winning_idx + lead_seat) % 5

        if card in trick:
            card_idx = trick.index(card)
            return (card_idx + lead_seat) % 5

        # winner always leads the next trick
        lead_seat = winner_seat
    raise ValueError
