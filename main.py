from dataclasses import dataclass
from drafter import *
from bakery import assert_equal

#constants below as provided by red cross
pH_max = 7.8
pH_min = 7.2
Chlorine_max = 10.0
Chlorine_min = 1.0

#first dataclass
@dataclass
class Reading:
    pool: str
    time: int
    ph: float
    chlorine: float
    guard: str
    date: int

#second dataclass
@dataclass
class State:
    readings: list[Reading]  #keeps track of every entry entered
    current_day: int         #day being viewed and will allow to inc/dec to move
    current_pool: str        #pool being viewed and changed by switch_pool
    unsafe_count: int        #counts up when unsafe reading is entered
    
#helper functions
def ph_is_safe(ph: float) -> bool:
    """true if in range and edge cases count"""
    if pH_min <= ph <= pH_max:
        return True
    return False


def chlorine_is_safe(chlorine: float) -> bool:
    """true if in range and edge cases count"""
    if Chlorine_min <= chlorine <= Chlorine_max:
        return True
    return False


def readings_for_day(readings: list[Reading], day: int, pool: str) -> list[Reading]:
    """the loop only keeps matches from day"""
    matches = []
    for reading in readings:
        if reading.date == day and reading.pool == pool:
            matches.append(reading)
    return matches


def reading_to_text(reading: Reading) -> str:
    """turns a readin ginto a readable line"""
    if ph_is_safe(reading.ph) and chlorine_is_safe(reading.chlorine):
        status = "SAFE"
    else:
        status = "UNSAFE"
    return (str(reading.time) + " | pH " + str(reading.ph) +
            " | Cl " + str(reading.chlorine) + " | Guard: " +
            reading.guard + " | " + status)

def is_number(text: str) -> bool:
    """true if text is digits with at most one dot."""
    if text == "" or text == ".":
        return False
    dots = 0
    for char in text:
        if char == ".":
            dots = dots + 1
        elif not char.isdigit():
            return False
    return dots <= 1

def next_pool(current: str) -> str:
    """switches between the two pools"""
    if current == "Main Pool":
        return "Kiddie Pool"
    return "Main Pool"


def show_readings(readings: list[Reading]) -> list[str]:
    """turns a list of readings into page lines"""
    if not readings:
        return ["No readings for this day yet."]
    lines = []
    for reading in readings:
        lines.append(reading_to_text(reading))
    return lines


#routes
@route
def index(state: State) -> Page:
    """First page - home page."""
    return Page(state, [
        Header("Pool Chemical Log"),
        "Current pool: " + state.current_pool,
        "Current day: " + str(state.current_day),
        "Unsafe readings so far: " + str(state.unsafe_count),
        Button("Log a reading", enter_reading),
        Button("Today's readings", todays_reading),
        Button("All past readings", past_reading),
        Button("Switch pool", switch_pool),
    ])
@route
def enter_reading(state: State) -> Page:
    """Second page - form with the 6 textboxes."""
    return Page(state, [
        Header("Enter a Reading"),
        "Pool:", TextBox("pool", state.current_pool),
        "Time (ex: 1030):", TextBox("time", ""),
        "pH:", TextBox("ph", ""),
        "Chlorine (ppm):", TextBox("chlorine", ""),
        "Guard name:", TextBox("guard", ""),
        "Day:", TextBox("date", str(state.current_day)),
        Button("Submit", check_reading),
        Button("Back", index),
    ])

@route
def check_reading(state: State, pool: str, time: str, ph: str,
                  chlorine: str, guard: str, date: str) -> Page:
    """Third page - results after submitting."""
    # stop bad input before float()/int() can crash the site
    if not (is_number(time) and is_number(ph) and
            is_number(chlorine) and is_number(date)):
        return Page(state, [
            Header("Error"),
            "Time, pH, chlorine, and day must all be numbers.",
            Button("Try again", enter_reading),
            Button("Home", index),
        ])

    new_reading = Reading(pool, int(float(time)), float(ph),
                          float(chlorine), guard, int(float(date)))
    state.readings.append(new_reading)

    if ph_is_safe(new_reading.ph):
        ph_message = "pH " + ph + " is SAFE"
    else:
        ph_message = "pH " + ph + " is UNSAFE"

    if chlorine_is_safe(new_reading.chlorine):
        chlorine_message = "Chlorine " + chlorine + " is SAFE"
    else:
        chlorine_message = "Chlorine " + chlorine + " is UNSAFE"

    if not (ph_is_safe(new_reading.ph) and chlorine_is_safe(new_reading.chlorine)):
        state.unsafe_count = state.unsafe_count + 1

    return Page(state, [
        Header("Reading Saved"),
        ph_message,
        chlorine_message,
        Button("Enter another", enter_reading),
        Button("Home", index),
    ])

@route
def todays_reading(state: State) -> Page:
    """Fourth page - readings for the current day and pool."""
    matches = readings_for_day(state.readings, state.current_day, state.current_pool)
    lines = show_readings(matches)
    return Page(state, [
        Header(state.current_pool + " - Day " + str(state.current_day)),
        "Unsafe readings so far: " + str(state.unsafe_count),
    ] + lines + [
        Button("Prev day", "prev_day"),
        Button("Next day", "next_day"),
        Button("Switch pool", "switch_pool"),
        Button("All past readings", "past_reading"),
        Button("Log a reading", "enter_reading"),
        Button("Home", "index"),
    ])


@route
def prev_day(state: State) -> Page:
    """goes back one day, but never below day 1"""
    if state.current_day > 1:
        state.current_day = state.current_day - 1
    return todays_reading(state)


@route
def next_day(state: State) -> Page:
    """goes forward one day"""
    state.current_day = state.current_day + 1
    return todays_reading(state)


@route
def switch_pool(state: State) -> Page:
    """flips to the other pool"""
    state.current_pool = next_pool(state.current_pool)
    return todays_reading(state)


@route
def past_reading(state: State) -> Page:
    """Fifth page - every reading for the current pool, all days"""
    lines = []
    for reading in state.readings:
        if reading.pool == state.current_pool:
            lines.append("Day " + str(reading.date) + " | " + reading_to_text(reading))
    if lines == []:
        lines = ["No readings for this pool yet."]
    return Page(state, [
        Header("All readings - " + state.current_pool),
    ] + lines + [
        Button("Back", "todays_reading"),
        Button("Home", "index"),
    ])

#unit tests
# ph_is_safe
assert_equal(ph_is_safe(7.4), True)    # in range
assert_equal(ph_is_safe(7.0), False)   # too low
assert_equal(ph_is_safe(8.2), False)   # too high
assert_equal(ph_is_safe(7.2), True)    # bottom edge
assert_equal(ph_is_safe(7.8), True)    # top edge

# chlorine_is_safe
assert_equal(chlorine_is_safe(3.0), True)    # in range
assert_equal(chlorine_is_safe(0.5), False)   # too low
assert_equal(chlorine_is_safe(12.0), False)  # too high
assert_equal(chlorine_is_safe(1.0), True)    # bottom edge
assert_equal(chlorine_is_safe(10.0), True)   # top edge

# readings_for_day
r1 = Reading("Main Pool", 900, 7.4, 3.0, "Sam", 1)
r2 = Reading("Main Pool", 1200, 7.0, 2.0, "Ava", 1)
r3 = Reading("Kiddie Pool", 900, 7.5, 2.5, "Sam", 1)
r4 = Reading("Main Pool", 900, 7.6, 3.5, "Ava", 2)
assert_equal(readings_for_day([], 1, "Main Pool"), [])                        # empty
assert_equal(readings_for_day([r3, r4], 1, "Main Pool"), [])                  # no matches
assert_equal(readings_for_day([r1, r2, r3, r4], 1, "Main Pool"), [r1, r2])    # some
assert_equal(readings_for_day([r1, r2, r3, r4], 1, "Kiddie Pool"), [r3])      # other pool

# reading_to_text
assert_equal(reading_to_text(r1), "900 | pH 7.4 | Cl 3.0 | Guard: Sam | SAFE")
assert_equal(reading_to_text(r2), "1200 | pH 7.0 | Cl 2.0 | Guard: Ava | UNSAFE")

#is_number
assert_equal(is_number("7.4"), True)     # decimal
assert_equal(is_number("1030"), True)    # whole number
assert_equal(is_number(""), False)       # empty
assert_equal(is_number("abc"), False)    # letters
assert_equal(is_number("7.4.1"), False)  # two dots
assert_equal(is_number("."), False)      # just a dot

#show_reading
assert_equal(show_readings([]), ["No readings for this day yet."])
assert_equal(show_readings([r1]), ["900 | pH 7.4 | Cl 3.0 | Guard: Sam | SAFE"])
assert_equal(show_readings([r1, r2]), [
    "900 | pH 7.4 | Cl 3.0 | Guard: Sam | SAFE",
    "1200 | pH 7.0 | Cl 2.0 | Guard: Ava | UNSAFE"
])

# next_pool
assert_equal(next_pool("Main Pool"), "Kiddie Pool")
assert_equal(next_pool("Kiddie Pool"), "Main Pool")

# prev_day / next_day change the state
s = State([], 1, "Main Pool", 0)
prev_day(s)
assert_equal(s.current_day, 1)   # can't go below 1
next_day(s)
assert_equal(s.current_day, 2)
prev_day(s)
assert_equal(s.current_day, 1)

#start server
start_server(State([], 1, "Main Pool", 0))

