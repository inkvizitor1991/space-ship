import asyncio
import curses
import random
import time
from functools import partial
from itertools import cycle

from curses_tools import draw_frame, get_frame_size, read_controls
from read_rocket_frame import read_rocket_frame

TIC_TIMEOUT = 0.1
ROCKET_STEP = 1
STARS = 100
SYMBOLS = '+*.:'


async def fire(canvas, start_row, start_column, rows_speed=-0.3, columns_speed=0):
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


async def blink(canvas, row, column, symbol):
    curses_state = (
        curses.A_DIM, curses.A_NORMAL,
        curses.A_BOLD, curses.A_NORMAL
    )
    stars_tic_timeout = (2, 0.3, 0.5, 0.3)
    offset_tics = random.randint(0, 10)

    for _ in range(offset_tics):
        await asyncio.sleep(0)

    while True:
        for state, tic_timeout in zip(curses_state, stars_tic_timeout):
            canvas.addstr(row, column, symbol, state)
            for _ in range(round(tic_timeout / 0.1)):
                await asyncio.sleep(0)


async def animate_spaceship(
        canvas, rocket_frame_start, rocket_frame_finish,
        rocket_row, rocket_column, row, column):

    rocket_frames = (
        rocket_frame_start, rocket_frame_start,
        rocket_frame_finish, rocket_frame_finish
    )
    for rocket_frame in cycle(rocket_frames):
        rows_direction, columns_direction, space_pressed = read_controls(
            canvas, ROCKET_STEP
        )
        size_rocket_rows, size_rocket_columns = get_frame_size(rocket_frame)

        rocket_row += rows_direction
        rocket_column += columns_direction

        rocket_row = max(1, min(rocket_row, row - size_rocket_rows))
        rocket_column = max(1, min(rocket_column, column - size_rocket_columns))

        draw_frame(canvas, rocket_row, rocket_column, rocket_frame)
        await asyncio.sleep(0)
        draw_frame(canvas, rocket_row, rocket_column, rocket_frame, negative=True)


def create_coroutines(rocket_frame_start, rocket_frame_finish, canvas):
    height, width = canvas.getmaxyx()
    row, column = height - 1, width - 1
    centre_row, centre_column = row // 2, column // 2

    coroutines = [
        blink(
            canvas, random.randint(1, row - 1),
            random.randint(1, column - 1),
            random.choice(SYMBOLS)
        )
        for _ in range(STARS + 1)
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
    canvas.nodelay(True)
    curses.curs_set(False)
    canvas.border()
    coroutines = create_coroutines(
        rocket_frame_first, rocket_frame_second, canvas
    )

    while True:
        for coroutine in coroutines.copy():
            try:
                coroutine.send(None)
            except StopIteration:
                coroutines.remove(coroutine)
        canvas.refresh()
        time.sleep(TIC_TIMEOUT)


if __name__ == '__main__':
    frames_folder = 'spaceship_frames/'
    rocket_frame_start, rocket_frame_finish = read_rocket_frame(frames_folder)
    curses.update_lines_cols()
    curses.wrapper(partial(run, rocket_frame_start, rocket_frame_finish))