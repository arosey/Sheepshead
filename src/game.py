import inspect
from enum import Enum
from typing import Optional
import logging

from src.data import (
    Hand,
    PickStyle,
    seat_with_card,
    tricks_taken_by_seat,
    Trick,
    winning_card_idx,
)
from src.deck import create_piquet_pack, Card
from src.player import Player, DefaultPlayer, HumanPlayer
from src.util import chunks, nth, random_name


class Outcome(Enum):
    """
    Point Total | Picker (Alone) | Picker (w/ Partner) | Partner | Opponents
    ------------------------------------------------------------------------------
    All Tricks  |	   +12 	     |         +6          |   +3    |   -3
    91 to 120   |	   +8 	     |         +4          |   +2    |   -2
    61 to 90    |	   +4 	     |         +2          |   +1    |   -1
    31 to 60    |	   -4 	     |         -2          |   -1    |	 +1
    0 to 30     |	   -8 	     |         -4          |   -2    |	 +2
    No Tricks   |	   -12       |	       -6          |   -3    |	 +3

    Points are given/taken on a zero-sum basis.
    The picker (and partner if there is one), need over half, i.e. 61, card points to win.
    Partner gains/pays half what the picker gains/pays.

    "Schneider" is something the loser gets by having at least either 30 or 31 points.
    If the picker loses, they have schneider with 31 or more points.
    If the opponents lose, they have schneider with 30 or more points
    The picker is said to have, "Won with schneider", if they got less than 91 points.

    https://en.wikipedia.org/wiki/Sheepshead_(card_game)#Scoring
    """

    WIN_ALL_TRICKS = 12
    WIN_NO_SCHNEIDER = 8
    WIN_WITH_SCHNEIDER = 4
    LOSE_WITH_SCHNEIDER = -4
    LOSE_NO_SCHNEIDER = -8
    Lose_NO_TRICKS = -12

    def __str__(self):
        return f"{self.name.capitalize().replace('_', ' ')}"

    def __repr__(self):
        return self.name.capitalize()


def play_trick(players: list[Player], hand: Hand, lead_seat: int) -> Hand:
    print(f"Beginning the {nth(len(hand) + 1)} trick")
    for i in range(5):
        under_the_gun = (lead_seat + i) % 5
        hand: Hand = players[under_the_gun].play(hand)
        verb = "plays" if i else "leads"
        print(f"{players[under_the_gun]} {verb} {hand[-1][-1]}")
    winning_idx = winning_card_idx(hand[-1], hand.called_card)
    winner_seat = (winning_idx + lead_seat) % 5
    print(f"{players[winner_seat].name} takes the trick with {hand[-1][winning_idx]}")
    return hand


def play_hand(
    players: list[Player], dealer_seat: int, blind: list[Card]
) -> Optional[Hand]:
    logging.debug(
        f"{inspect.getframeinfo(inspect.currentframe()).function}("
        f"{', '.join([f'{k}={v}' for k, v in inspect.currentframe().f_locals.items()])}"
        f")"
    )

    lead_seat = (dealer_seat + 1) % 5
    picker = None
    for i in range(5):
        under_the_gun = (lead_seat + i) % 5
        print(f"{players[under_the_gun]} is given the option to pick")
        if players[under_the_gun].wants_to_pick:
            picker = players[under_the_gun]
            break
    if picker is None:
        return None
    style, called_card = picker.pick(blind)
    assert called_card is None if style == PickStyle.ALONE else called_card is not None

    picker_description = (
        "is going alone"
        if style == PickStyle.ALONE
        else f"chooses {style} with {called_card} as partner"
    )
    print(f"{picker.name} picks and {picker_description}")
    for player in players:
        player.update_picker_choice(style, called_card)

    hand = Hand(dealer_seat, picker.seat, style, called_card)
    lead_seat = (dealer_seat + 1) % 5
    for _ in range(6):
        hand = play_trick(players, hand, lead_seat)
        winning_idx = winning_card_idx(hand[-1], hand.called_card)
        lead_seat = (winning_idx + lead_seat) % 5

    return hand


def deal(players: list[Player], dealer_seat: int) -> list[Card]:
    """
    Deals six cards to each player
    :returns: The blind
    """
    print(f"{players[dealer_seat]} is the dealer")
    assert len(players) == 5
    cards = create_piquet_pack()
    card_gen = chunks(cards, 6)
    lead_seat = (dealer_seat + 1) % 5
    for i in range(5):
        up_next = (lead_seat + i) % 5
        players[up_next].get_deal(next(card_gen))
    return next(card_gen)


def update_scores_alone(players: list[Player], hand: Hand):
    assert hand.pick_style == PickStyle.ALONE and hand.called_card is None
    tricks_taken_by_picker: list[Trick] = tricks_taken_by_seat(hand, hand.picker_seat)
    picker = players[hand.picker_seat]
    picker_points = picker.points_taken
    outcome = None
    if len(tricks_taken_by_picker) == 6:
        # If the picker takes all 6 tricks, they will have 120 points.
        # However, having 120 points does guarantee they took every trick as they could have lost a 0-point trick
        outcome = Outcome.WIN_ALL_TRICKS
    elif len(tricks_taken_by_picker) == 0:
        # Having 0 points does not guarantee they took no tricks as they could have taken a 0-point trick.
        # Having more than 0 points does not guarantee they took a trick as the points could come from their bury.
        outcome = Outcome.Lose_NO_TRICKS
    elif picker_points >= 91:
        outcome = Outcome.WIN_NO_SCHNEIDER
    elif picker_points >= 61:
        outcome = Outcome.WIN_WITH_SCHNEIDER
    elif picker_points >= 31:
        outcome = Outcome.LOSE_WITH_SCHNEIDER
    else:
        assert 0 <= picker_points <= 30
        outcome = Outcome.LOSE_NO_SCHNEIDER

    print(f"Picker {picker.name} {outcome}")
    print("|".join([f"{player.name: ^16}" for player in players]))
    picker_delta = outcome.value
    opposition_delta = outcome.value / -4
    delta_strings = [""] * len(players)
    for i in range(len(players)):
        delta = picker_delta if players[i] is picker else opposition_delta
        players[i].score += delta
        delta_strings[i] = f"{f'{players[i].score}({delta})': ^16}"
    print("|".join(delta_strings))
    print()


def update_scores_partnered(players, hand):
    assert hand.pick_style != PickStyle.ALONE and hand.called_card is not None
    partner_seat = seat_with_card(hand, hand.called_card)
    tricks_taken_by_picker_team = tricks_taken_by_seat(
        hand, hand.picker_seat, partner_seat
    )
    partner = players[partner_seat]
    picker = players[hand.picker_seat]
    picker_team_points = partner.points_taken + picker.points_taken
    outcome = None
    if len(tricks_taken_by_picker_team) == 6:
        # If the picker takes all 6 tricks, they will have 120 points.
        # However, having 120 points does guarantee they took every trick as they could have lost a 0-point trick
        outcome = Outcome.WIN_ALL_TRICKS
    elif not tricks_taken_by_picker_team:
        # Having 0 points does not guarantee they took no tricks as they could have taken a 0-point trick.
        # Having more than 0 points does not guarantee they took a trick as the points could come from their bury.
        outcome = Outcome.Lose_NO_TRICKS
    elif picker_team_points >= 91:
        outcome = Outcome.WIN_NO_SCHNEIDER
    elif picker_team_points >= 61:
        outcome = Outcome.WIN_WITH_SCHNEIDER
    elif picker_team_points >= 31:
        outcome = Outcome.LOSE_WITH_SCHNEIDER
    else:
        assert 0 <= picker_team_points <= 30
        outcome = Outcome.LOSE_NO_SCHNEIDER

    print(f"Picker {picker.name} {outcome}")
    print("|".join([f"{player.name: ^16}" for player in players]))
    picker_delta = outcome.value / 2
    partner_delta = outcome.value / 4
    opposition_delta = outcome.value / -4
    delta_strings = [""] * len(players)
    for i in range(len(players)):
        delta = (
            picker_delta
            if players[i] is picker
            else partner_delta if players[i] is partner else opposition_delta
        )
        players[i].score += delta
        delta_strings[i] = f"{f'{players[i].score}({delta})': ^16}"
    print("|".join(delta_strings))
    print()


def update_scores(players: list[Player], hand: Hand):
    if hand.pick_style == PickStyle.ALONE:
        update_scores_alone(players, hand)
    else:
        update_scores_partnered(players, hand)


def play_game(
    auto: bool, spectate: bool, number_of_hand: int, player_names: Optional[list[str]]
):
    logging.debug(
        f"{inspect.getframeinfo(inspect.currentframe()).function}("
        f"{', '.join([f'{k}={v}' for k, v in inspect.currentframe().f_locals.items()])}"
        f")"
    )
    player_names: list[str] = player_names if player_names else []
    if len(player_names) < 5:
        name_gen = random_name()
        player_names += [next(name_gen) for _ in range(5 - len(player_names))]
    players: list[Player] = [DefaultPlayer(player_names[i], i) for i in range(5)]

    if not spectate:
        name = input("Enter your name:").strip().replace(" ", "_")
        players[0] = HumanPlayer(name, 0, auto=auto)

    for i in range(number_of_hand):
        dealer_seat = i % 5
        blind: list[Card] = deal(players, dealer_seat)
        result: Optional[Hand] = play_hand(players, dealer_seat, blind)
        if result is None:
            # TODO: No picker scenarios
            print("All players pass")
            continue
        update_scores(players, result)
        for j in range(5):
            players[j] = players[j].reset()
