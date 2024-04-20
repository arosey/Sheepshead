import random
from typing import Generator, TypeVar, Optional

_T = TypeVar("_T")


def chunks(xs: list[_T], n: int) -> Generator[list[_T], None, None]:
    """Yield successive n-sized chunks"""
    for i in range(0, len(xs), n):
        yield xs[i : i + n]


def nth(num: int) -> str:
    """
    Returns the number with an ordinal indicator. e.g.
    1 -> 1st, 2 -> 2nd, 3 -> 3rd, etc.
    """
    if 3 < num < 21:
        # 11 - 13 are exceptions
        return f"{num}th"
    num_str = str(num)
    last_digit = num_str[-1]
    match last_digit:
        case "1":
            return num_str + "st"
        case "2":
            return num_str + "nd"
        case "3":
            return num_str + "rd"
        case _:
            return num_str + "th"


def pop_random(xs: list[_T], illegal: Optional[_T] = None) -> _T:
    """
    Pops a random element.
    Will pop illegal if it is the only element in xs.

    :raises: ValueError if illegal not in xs
    """
    i = random.randrange(len(xs))
    if illegal is not None and i == xs.index(illegal):
        i = (i + 1) % len(xs)

    return xs.pop(i)


def get_random(xs: list[_T]) -> Generator[_T, None, None]:
    """
    Yields random element. Does not maintain element order. Does not remove elements from xs
    """
    pos = len(xs)

    while pos > 0:
        idx = random.randrange(pos)

        pos -= 1
        if idx != pos:
            xs[pos], xs[idx] = xs[idx], xs[pos]

        yield xs[pos]


def random_name() -> Generator[str, None, None]:
    """
    Yields random name
    """
    names = [
        "Audra",
        "Aeris",
        "Aster",
        "Agnes",
        "Andra",
        "Aylin",
        "Blyth",
        "Cecil",
        "Casia",
        "Celia",
        "Clove",
        "Clark",
        "Daria",
        "Doris",
        "Darcy",
        "Delia",
        "Elsie",
        "Elise",
        "Eliza",
        "Ester",
        "Edith",
        "Elena",
        "Ethel",
        "Fauna",
        "Fiona",
        "Haven",
        "Hazel",
        "Junia",
        "Jessa",
        "Josie",
        "Jules",
        "Lucia",
        "Livia",
        "Leola",
        "Leona",
        "Leone",
        "Lydia",
        "Layla",
        "Lilia",
        "Lorna",
        "Lilah",
        "Lilac",
        "Lovey",
        "Mavis",
        "Mabel",
        "Micha",
        "Maude",
        "Misty",
        "Macey",
        "Milan",
        "Olene",
        "Olina",
        "Piper",
        "Quinn",
        "Reece",
        "Roses",
        "Tawny",
        "Twila",
        "Tansy",
        "Velma",
        "Verna",
        "Veryn",
        "Willa",
        "Wendy",
        "Wanda",
        "Zilah",
        "Angus",
        "Ansel",
        "Alton",
        "Alvey",
        "Aiden",
        "Arten",
        "Alvin",
        "Alder",
        "Atlas",
        "Briar",
        "Bowen",
        "Bryce",
        "Baron",
        "Caleb",
        "Clyde",
        "Clint",
        "Cecil",
        "Clark",
        "Drake",
        "Elton",
        "Ervin",
        "Elvis",
        "Edwin",
        "Elmer",
        "Ellis",
        "Elrid",
        "Elric",
        "Flynn",
        "Flint",
        "Glenn",
        "Glynn",
        "Gomer",
        "Heath",
        "Hayes",
        "Isaac",
        "Jaxon",
        "Jonah",
        "Jones",
        "Jonas",
        "Keith",
        "Klaus",
        "Knoll",
        "Klein",
        "Linus",
        "Lloyd",
        "Leroy",
        "Lewis",
        "Myles",
        "Moore",
        "Micah",
        "Nigel",
        "Nolan",
        "Orris",
        "Odeon",
        "Oakes",
        "Orson",
        "Percy",
        "Piers",
        "Quinn",
        "Ralph",
        "Rufus",
        "Regis",
        "Remus",
        "Reece",
        "Rowan",
        "Simon",
        "Silas",
        "Tomis",
        "Tatum",
        "Verne",
        "Wells",
        "Wyatt",
        "Wayne",
    ]

    return get_random(names)
