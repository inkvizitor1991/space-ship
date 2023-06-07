import asyncio
import curses
import random
import time
from functools import partial
from itertools import cycle

from curses_tools import draw_frame, get_frame_size, read_controls
from read_rocket_frame import read_rocket_frame


STEP_UP = 1
STEP_DOWN = 1
STEP_RIGHT = 1
STEP_LEFT = 1

COUNT_STARTS = 100
SYMBOLS = '+*.:'


async def fire(canvas, start_row, start_column, rows_speed=-0.3,
               columns_speed=0):
    """Display animation of gun shot, direction and speed can be specified."""

    row, column = start_row, start_column

    canvas.addstr(round(row), round(column), '*')
    await asyncio.sleep(0)

    canvas.addstr(round(row), round(column), 'O')
    await asyncio.sleep(0)
    canvas.addstr(round(row), round(column), ' ')

    row += rows_speed
    column += columns_speed

    symbol = '-' if columns_speed else '|'

    rows, columns = canvas.getmaxyx()
    max_row, max_column = rows - 1, columns - 1

    curses.beep()

    while 0 < row < max_row and 0 < column < max_column:
        canvas.addstr(round(row), round(column), symbol)
        await asyncio.sleep(0)
        canvas.addstr(round(row), round(column), ' ')
        row += rows_speed
        column += columns_speed


async def blink(canvas, curses_state, row, column, symbol):

    while True:
        for state in curses_state:
            canvas.addstr(row, column, symbol, state)
            for number in range(random.randint(0, 5)):
                await asyncio.sleep(0)


async def animate_spaceship(
        canvas, rocket_frame_start, rocket_frame_finish,
        rocket_row, rocket_column, row, column):

    for rocket_frame in cycle((rocket_frame_start, rocket_frame_finish)):
        canvas.nodelay(True)
        rows_direction, columns_direction, space_pressed = read_controls(
            canvas, STEP_UP, STEP_DOWN, STEP_RIGHT, STEP_LEFT
        )
        size_rocket_rows, size_rocket_columns = get_frame_size(rocket_frame)

        state_column = rocket_column
        state_row = rocket_row
        rocket_row += rows_direction
        rocket_column += columns_direction

        if rocket_column + size_rocket_columns >= column or rocket_column <= 0:
            rocket_column = state_column

        if rocket_row + size_rocket_rows >= row or rocket_row <= 0:
            rocket_row = state_row

        draw_frame(canvas, rocket_row, rocket_column, rocket_frame)
        canvas.refresh()
        await asyncio.sleep(0)
        draw_frame(canvas, rocket_row, rocket_column, rocket_frame, negative=True)


def create_coroutines(rocket_frame_start, rocket_frame_finish, canvas):
    row, column = canvas.getmaxyx()
    centre_row, centre_column = row // 2, column // 2
    courses_state = (
        curses.A_DIM, curses.A_NORMAL,
        curses.A_BOLD, curses.A_NORMAL
    )

    coroutines = [
        blink(
            canvas, courses_state, random.randint(1, row - 1),
            random.randint(1, column - 1),
            random.choice(SYMBOLS)
        )
        for _ in range(COUNT_STARTS + 1)
    ]

    start_fire = fire(canvas, centre_row, centre_column)

    spaceship = animate_spaceship(
        canvas, rocket_frame_start,
        rocket_frame_finish, centre_row,
        centre_column, row, column
    )
    coroutines.append(spaceship)
    coroutines.append(start_fire)
    return coroutines


def run(rocket_frame_first, rocket_frame_second, canvas):
    sleep_time = (2, 0.3, 0.5, 0.3)
    coroutines = create_coroutines(
        rocket_frame_first, rocket_frame_second, canvas
    )

    while True:

        for second in sleep_time:
            try:
                for coroutine in coroutines:
                    coroutine.send(None)
            except StopIteration:
                coroutines.remove(coroutine)
            canvas.border()
            curses.curs_set(False)
            canvas.refresh()
            time.sleep(second)


if __name__ == '__main__':
    frames_folder = 'spaceship_frames/'
    rocket_frame_start, rocket_frame_finish = read_rocket_frame(frames_folder)
    curses.update_lines_cols()
    curses.wrapper(partial(run, rocket_frame_start, rocket_frame_finish))
