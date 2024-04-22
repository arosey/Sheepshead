import inspect
import logging
import random
from typing import Optional, Tuple

from src.data import Hand, PickStyle, Trick
from src.deck import Card, Power, Suit
from src.util import pop_random


class Player:
    def __init__(self, name: str, seat: int, score: int = 0):
        """
        :raises ValueError: if seat < 0 or seat > 4
        """
        if seat < 0 or 4 < seat:
            raise ValueError(f"Expected seat between 0-4 but {seat} was given")

        self.name = name
        self.seat = seat
        self.score = score
        self._tricks: list[Trick] = []
        self._dealt_cards: list[Card] = []
        self._bury: Optional[list[Card]] = None
        self._partner_seat: Optional[int] = None
        self._partner_is_known: Optional[bool] = False

    def __str__(self):
        description = ""
        if self.is_picker:
            description += "(picker)"
        elif self.is_partner and self._partner_is_known:
            description += "(partnr)"
        else:
            description += f"(seat {self.seat})"
        return f"{self.name.capitalize()} {description}"

    def take(self, trick: Trick):
        """
        Reveals all cards in the trick and saves them to the list of tricks taken.
        A hidden or under card is only visible to the player who takes the trick containing it.
        """
        logging.debug(
            f"{inspect.getframeinfo(inspect.currentframe()).function}("
            f"{', '.join([f'{k}={v}' for k, v in inspect.currentframe().f_locals.items()])}"
            f")"
        )
        assert len(trick) == 5
        taken = trick
        if any(card.is_hidden for card in trick):
            revealed_cards = [card.reveal() for card in trick]
            taken = Trick(revealed_cards)
        self._tricks.append(taken)

    def get_deal(self, cards: list[Card]):
        """
        Each of the five players receive six cards. Typically, cards are dealt three to each player, two to the blind,
        and three to each player again. However, dealing all six at once is also acceptable.
        """
        logging.debug(
            f"{inspect.getframeinfo(inspect.currentframe()).function}("
            f"{', '.join([f'{k}={v}' for k, v in inspect.currentframe().f_locals.items()])}"
            f")"
        )
        assert len(cards) == len(set(cards)) == 6
        self._dealt_cards = cards
        self._dealt_cards.sort(key=lambda c: c.power)

    def pick(self, blind: list[Card]) -> Tuple[PickStyle, Optional[Card]]:
        """
        The picker chooses a called ace suit after picking the blind. Whoever has this called ace will be his partner.
        There are a few further rules behind this.
        1) The called suit must be a fail suit (clubs, spades or hearts).
        2) The picker must have at least one of the fail suit in his/her hand. The picker must keep at least one card of
        the fail suit in his hand (i.e. cannot throw them all off) until the first trick for which that suit is led, and
        then of course must follow suit. Also on the first trick for which that suit is led, the partner must play the
        ace (even if the player has another card of that suit).
            a) If the picker has all 3 fail aces, he may call a 10 instead of an ace. The picker is obligated to hold
            the ace of that suit in his hand. When the called suit is led, the picker must play the ace. In addition,
            the person with the 10 takes the trick if it is not trumped.
            b) If the picker does not have all 3 fail aces but has no fail suits for which he or she does not also have
            the ace, the picker may still call another fail suit's ace and utilize an "unknown." The picker lays a card
            face down (typically a low fail card or their lowest trump) and calls a fail suit for the unknown to
            represent. The unknown is played face down and has no power to take tricks, though its point value remains
            at the end of the game. Only the player taking the unknown is allowed to look at it until the end of the
            game.
            c) In some variants, the picker can call a suit for which he has the ace; he must save the ace, and then he
            is his own "secret" partner. NOT allowed in this implementation!
        3) The picker can choose to go alone after picking up the blind. In this case, there will be no called ace.
        https://en.wikipedia.org/wiki/Sheepshead_(card_game)#Called_Ace
        """
        logging.debug(
            f"{inspect.getframeinfo(inspect.currentframe()).function}("
            f"{', '.join([f'{k}={v}' for k, v in inspect.currentframe().f_locals.items()])}"
            f")"
        )
        return self._pick_internal(blind)

    def play(self, hand: Hand) -> Hand:
        """
        Players must follow suit if they can.
        There are further restrictions on when the picker and partner can play their called suit cards:
        1) The picker must keep a fail of the called suit until it is lead.
        2) The partner must keep the called card until its suit is lead.
        3) The called card takes the trick the first time the called suit is lead unless trumped (see called ten).
        4) The partner must play the called card the first time its suit is lead.
        """
        logging.debug(
            f"{inspect.getframeinfo(inspect.currentframe()).function}("
            f"{', '.join([f'{k}={v}' for k, v in inspect.currentframe().f_locals.items()])}"
            f")"
        )
        logging.debug(f"{self.name}'s cards: {self._dealt_cards}")
        assert len(self._dealt_cards) == len(set(self._dealt_cards))
        if self.is_partner and hand.called_card not in self._dealt_cards:
            self._partner_is_known = True
        return self._play_internal(hand)

    def reset(self):
        """
        Returns a new instance of this class with the same name, seat, and score
        """
        logging.debug(
            f"{inspect.getframeinfo(inspect.currentframe()).function}("
            f"{', '.join([f'{k}={v}' for k, v in inspect.currentframe().f_locals.items()])}"
            f")"
        )
        if type(self) == Player:
            return type(self)(self.name, self.seat, self.score)
        return self._reset_internal()

    def update_picker_choice(self, style: PickStyle, called_card: Optional[Card]):
        """
        All players need to know the picker's choice before the first trick.
        """
        logging.debug(
            f"{inspect.getframeinfo(inspect.currentframe()).function}("
            f"{', '.join([f'{k}={v}' for k, v in inspect.currentframe().f_locals.items()])}"
            f")"
        )
        if called_card in self._dealt_cards:
            self._partner_seat = self.seat
        return self._update_picker_choice_internal(style, called_card)

    @property
    def points_taken(self):
        points_from_tricks = sum([trick.points for trick in self._tricks])
        points_from_bury = 0
        if self._bury is not None:
            points_from_bury = sum([c.points for c in self._bury])
        return points_from_tricks + points_from_bury

    @property
    def is_partner(self):
        return self.seat == self._partner_seat

    @property
    def is_picker(self):
        return self._bury is not None

    @property
    def is_opposition(self):
        return not (self.is_picker or self.is_partner)

    @property
    def wants_to_pick(self):
        return self._wants_to_pick_internal

    @property
    def _wants_to_pick_internal(self):
        raise NotImplementedError

    def _pick_internal(self, blind: list[Card]) -> Tuple[PickStyle, Optional[Card]]:
        raise NotImplementedError

    def _play_internal(self, hand: Hand) -> Hand:
        raise NotImplementedError

    def _update_picker_choice_internal(
        self, style: PickStyle, called_card: Optional[Card]
    ):
        raise NotImplementedError

    def _reset_internal(self):
        raise NotImplementedError


class DefaultPlayer(Player):
    """
    A basic implementation of the player interface.
    Follows the rules but plays randomly.
    """

    def __init__(self, name: str, seat: int, **kwargs):
        self._play_strategy: PlayStrategy = PlayStrategy()
        super().__init__(name, seat, **kwargs)

    def _pick_internal(self, blind: list[Card]) -> Tuple[PickStyle, Optional[Card]]:
        if random.Random().random() <= 0.25:
            self._bury = blind
            return PickStyle.ALONE, None

        self._dealt_cards.extend(blind)

        trump: set[Card] = {c for c in self._dealt_cards if c.is_trump}
        fail: set[Card] = set(self._dealt_cards) - trump
        if not fail:
            # No fail cards.
            # Bury random cards and call under
            self._bury = [
                self._dealt_cards.pop(),
                self._dealt_cards.pop(),
            ]
            self._unknown = self._dealt_cards.pop()
            self._unknown = Card(
                self._unknown.suit,
                self._unknown.power,
                _mask=random.choice(list(Suit.fail_suits())),
            )
            called_card = Card(self._unknown.suit, Power.ACE)
            return PickStyle.UNDER, called_card

        fail_aces: set[Card] = {f for f in fail if f.power == Power.ACE}
        if not fail_aces:
            # No fail aces.
            # Any fail can serve as match to partner's ace
            fail_to_keep = next(c for c in fail)
            self._dealt_cards.remove(fail_to_keep)
            self._bury = [self._dealt_cards.pop(), self._dealt_cards.pop()]
            self._dealt_cards.append(fail_to_keep)

            called_card = Card(fail_to_keep.suit, Power.ACE)
            return PickStyle.CALLED_ACE, called_card

        if len(fail_aces) == 3:
            # We have all the fail aces.

            fail_tens = {f for f in fail if f.power == Power.TEN}
            if len(fail_tens) == 3:
                # extremely unlikely to have all fail aces AND all fail tens... not sure but I assume the picker would
                # be forced to go alone if it ever happened
                return PickStyle.ALONE, None

            fail_ten_suits = {c.suit for c in fail_tens}
            chosen_fail_ace: Card = next(
                ace for ace in fail_aces if ace.suit not in fail_ten_suits
            )

            self._dealt_cards.remove(chosen_fail_ace)
            self._bury = [self._dealt_cards.pop(), self._dealt_cards.pop()]
            self._dealt_cards.append(chosen_fail_ace)

            called_card = Card(chosen_fail_ace.suit, Power.TEN)
            return PickStyle.CALLED_TEN, called_card

        fail_suits: set[Suit] = {f.suit for f in fail}
        fail_ace_suits: set[Suit] = {s.suit for s in fail_aces}
        fail_suits_without_an_ace: set[Suit] = {
            s for s in fail_suits if s not in fail_ace_suits
        }
        if fail_suits_without_an_ace:
            # There is at least one fail suit for which we do not have the matching ace.
            # Select the first valid fail and call partner as the ace of that fail suit.
            fail_to_keep = next(c for c in fail if c.suit in fail_suits_without_an_ace)

            self._dealt_cards.remove(fail_to_keep)
            self._bury = [self._dealt_cards.pop(), self._dealt_cards.pop()]
            self._dealt_cards.append(fail_to_keep)

            called_card = Card(fail_to_keep.suit, Power.ACE)
            return PickStyle.CALLED_ACE, called_card

        # We do not have all the fail aces. However, we have all the aces for the fail suits do we have.
        # Go under with a suit for which we do not have the ace.
        self._bury = [self._dealt_cards.pop(), self._dealt_cards.pop()]
        possible_under_suits = list(Suit.fail_suits() - fail_ace_suits)
        any_card = self._dealt_cards.pop()
        under = Card(
            any_card.suit,
            any_card.power,
            _mask=random.choice(possible_under_suits),
        )
        self._dealt_cards.append(under)
        called_card = Card(under.suit, Power.ACE)
        return PickStyle.UNDER, called_card

    def _play_internal(self, hand: Hand) -> Hand:
        if not len(hand) or not len(hand[-1]) or hand[-1].is_full:
            return self._play_strategy.lead(self._dealt_cards, hand)
        return self._play_strategy.follow(self._dealt_cards, hand)

    def _update_picker_choice_internal(
        self, style: PickStyle, called_card: Optional[Card]
    ):
        if called_card in self._dealt_cards:
            self._play_strategy = PartnerStrategy()
        elif self.is_picker:
            if style == PickStyle.ALONE:
                self._play_strategy = OppositionStrategy()
            elif style == PickStyle.UNDER:
                self._play_strategy = CalledUnderPickerStrategy()
            elif style == PickStyle.CALLED_ACE:
                self._play_strategy = CalledAcePickerStrategy()
            else:
                assert style == PickStyle.CALLED_TEN
                self._play_strategy = CalledTenPickerStrategy()
        else:
            assert self.is_opposition
            self._play_strategy = OppositionStrategy()

    def _reset_internal(self):
        return type(self)(self.name, self.seat, score=self.score)

    @property
    def _wants_to_pick_internal(self):
        return random.Random().random() < 0.2


def lead_random(cards: list[Card], hand: Hand, illegal: Optional[Card] = None) -> Hand:
    """
    Plays a random card. Will play the illegal card if it is the only remaining choice.
    """
    return hand.play(pop_random(cards, illegal))


def follow_random(
    cards: list[Card], hand: Hand, fallback: Optional[Card] = None
) -> Hand:
    """
    Follows the lead suit with a random card. Play the fallback iff it is the only remaining choice.
    """
    if len(cards) == 1:
        # This should probably be an argument error, BUT I want it this way so sue me
        fallback = None

    lead_card: Card = hand[-1][0]
    followers = (
        {c for c in cards if c.is_trump}
        if lead_card.is_trump
        else {c for c in cards if c.suit == lead_card.suit and c.is_fail}
    )
    card = followers.pop() if followers else (set(cards) - {fallback}).pop()
    cards.remove(card)
    return hand.play(card)


class PlayStrategy:
    def lead(self, cards: list[Card], hand: Hand) -> Hand:
        assert not len(hand) or not len(hand[-1]) or hand[-1].is_full
        assert len(cards) == (6 - len(hand))

        if len(cards) == 1:
            return hand.play(cards.pop())
        return self._lead_internal(cards, hand)

    def follow(self, cards: list[Card], hand: Hand) -> Hand:
        assert len(hand) and len(hand[-1]) and not hand[-1].is_full
        assert len(cards) == (7 - len(hand))

        if len(cards) == 1:
            return hand.play(cards.pop())
        return self._follow_internal(cards, hand)

    def _lead_internal(self, cards: list[Card], hand: Hand) -> Hand:
        raise NotImplementedError

    def _follow_internal(self, cards: list[Card], hand: Hand) -> Hand:
        raise NotImplementedError


class CalledTenPickerStrategy(PlayStrategy):
    def _lead_internal(self, cards: list[Card], hand: Hand) -> Hand:
        """
        Similar to how the partner leads.
        If the called suit has not been lead, and the picker leads the called suit, they must do so with the called ace.
        The picker can play any card if the called suit as already been lead in a previous trick.
        """
        compliment = next(
            (
                c
                for c in cards
                if c.is_fail
                and c.suit == hand.called_card.suit
                and c.power == Power.ACE
            ),
            None,
        )
        if compliment is None:
            return lead_random(cards, hand)

        card = random.choice(cards)
        if card.is_fail and card.suit == compliment.suit:
            card = compliment

        cards.remove(card)
        return hand.play(card)

    def _follow_internal(self, cards: list[Card], hand: Hand) -> Hand:
        """
        Similar to how the partner follows.
        The picker must play the called ace if they have it and the called suit is led
        """
        compliment = next(
            (
                c
                for c in cards
                if c.is_fail
                and c.suit == hand.called_card.suit
                and c.power == Power.ACE
            ),
            None,
        )
        lead_card = hand[-1][0]
        if compliment and lead_card.is_fail and lead_card.suit == hand.called_card.suit:
            cards.remove(compliment)
            return hand.play(compliment)

        return follow_random(cards, hand, compliment)


class CalledAcePickerStrategy(PlayStrategy):
    def _lead_internal(self, cards: list[Card], hand: Hand) -> Hand:
        """
        random
        """
        return lead_random(cards, hand)

    def _follow_internal(self, cards: list[Card], hand: Hand) -> Hand:
        """
        The picker must hold onto a fail of the called suit until that suit is led.
        After the called suit is led, the picker can play anything (following the usual follow rules of course)
        """
        leads: list[Card] = [trick[0] for trick in hand]
        called_has_been_led = any(
            c for c in leads if c.is_fail and c.suit == hand.called_card.suit
        )
        if not called_has_been_led:
            compliment = next(
                c for c in cards if c.is_fail and c.suit == hand.called_card.suit
            )
            return follow_random(cards, hand, compliment)
        return follow_random(cards, hand)


class CalledUnderPickerStrategy(PlayStrategy):
    def _lead_internal(self, cards: list[Card], hand: Hand) -> Hand:
        """
        random.
        """
        return lead_random(cards, hand)

    def _follow_internal(self, cards: list[Card], hand: Hand) -> Hand:
        """
        The under card will be the only fail of the called suit the picker has.
        They are not allow to throw out their under card until the called suit is led at which time they must play it.
        """
        leads: list[Card] = [trick[0] for trick in hand]
        called_has_been_led = any(
            c for c in leads if c.is_fail and c.suit == hand.called_card.suit
        )
        if not called_has_been_led:
            compliment = next(
                c
                for c in cards
                if c.is_fail and c.suit == hand.called_card.suit and c.is_hidden
            )
            return follow_random(cards, hand, compliment)
        return follow_random(cards, hand)


class PartnerStrategy(PlayStrategy):
    def _lead_internal(self, cards: list[Card], hand: Hand) -> Hand:
        """
        If the called suit has not been lead, and the partner leads the called suit, they must do so with the called
        card. The partner can play any card if the called suit as already been lead in a previous trick.
        """
        card = random.choice(cards)
        if (
            hand.called_card in cards
            and card.is_fail
            and card.suit == hand.called_card.suit
        ):
            card = hand.called_card

        cards.remove(card)
        return hand.play(card)

    def _follow_internal(self, cards: list[Card], hand: Hand) -> Hand:
        """
        The partner must play the called ace if they have it and the called suit is led
        """
        lead_card = hand[-1][0]
        if (
            hand.called_card in cards
            and lead_card.is_fail
            and lead_card.suit == hand.called_card.suit
        ):
            cards.remove(hand.called_card)
            return hand.play(hand.called_card)

        return follow_random(cards, hand, hand.called_card)


class OppositionStrategy(PlayStrategy):
    def _lead_internal(self, cards: list[Card], hand: Hand) -> Hand:
        return lead_random(cards, hand)

    def _follow_internal(self, cards: list[Card], hand: Hand) -> Hand:
        return follow_random(cards, hand)


class HumanPlayer(Player):
    """
    Takes input to make decisions.
    """

    # TODO: Prevent the user from making illegal moves

    def __init__(self, name: str, seat: int, auto: bool, **kwargs):
        self.auto = auto
        super().__init__(name, seat, **kwargs)

    def __str__(self):
        return f"{self.name.capitalize()} (you)"

    def _pick_internal(self, blind: list[Card]) -> Tuple[PickStyle, Optional[Card]]:
        print(f"Blind: {blind[0]}, {blind[1]}")
        self._dealt_cards.extend(blind)
        self._bury = []
        while len(self._bury) < 2:
            chosen_card_idx = None
            indexed_cards = [f"{i}: {c}" for i, c in enumerate(self._dealt_cards)]
            user_input = input(
                "Select a card to bury\n" + "\t".join(indexed_cards) + "\n"
            )

            try:
                idx = int(user_input)
                if 0 <= idx < len(self._dealt_cards):
                    chosen_card_idx = idx
                else:
                    raise IndexError
            except ValueError:
                try:
                    card = Card.from_string(user_input)
                    chosen_card_idx = self._dealt_cards.index(card)
                    break
                except ValueError:
                    pass
            except IndexError:
                pass

            if chosen_card_idx is not None:
                self._bury.append(self._dealt_cards.pop(chosen_card_idx))
                print("Bury: " + "\t".join([str(c) for c in self._bury]))

        return PickStyle.ALONE, None

    def _play_internal(self, hand: Hand):
        indexed_cards = [f"{i}: {c}" for i, c in enumerate(self._dealt_cards)]
        chosen_card_idx = None
        while chosen_card_idx is None:
            user_input = input(
                "Select a card\n" + "\t".join(indexed_cards) + "\n"
            ).strip()
            try:
                idx = int(user_input)
                if 0 <= idx < len(self._dealt_cards):
                    chosen_card_idx = idx
                else:
                    raise IndexError
            except ValueError:
                try:
                    card = Card.from_string(user_input)
                    chosen_card_idx = self._dealt_cards.index(card)
                    break
                except ValueError:
                    pass
            except IndexError:
                pass
        hand.play(self._dealt_cards.pop(chosen_card_idx))

    def _reset_internal(self):
        return type(self)(self.name, self.seat, score=self.score, auto=self.auto)

    def _update_picker_choice_internal(
        self, style: PickStyle, called_card: Optional[Card]
    ):
        if self.is_picker:
            return
        print(
            f"You are {'' if called_card in self._dealt_cards else 'NOT '}the partner"
        )

    @property
    def _wants_to_pick_internal(self):
        while True:
            response = input("Do you want to pick? (y/n)\n").strip().lower()
            if "y" in response:
                return True
            elif "n" in response:
                return False
