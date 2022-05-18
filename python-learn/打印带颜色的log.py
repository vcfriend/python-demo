class Color:
    Black = 0
    Red = 1
    Green = 2
    Yellow = 3
    Blue = 4
    Magenta = 5
    Cyan = 6
    White = 7


class Mode:
    Foreground = 30
    Background = 40
    ForegroundBright = 90
    BackgroundBright = 100


def tcolor(c, m=Mode.Foreground):
    return '\033[{}m'.format(m + c)


def treset():
    return '\033[0m'


if __name__ == '__main__':
    import os

    os.system('')

    # usage
    print(tcolor(Color.Red) + 'hello' + treset())
    print(tcolor(Color.Green, Mode.Background) + 'color' + treset())
    print()

    COLOR_NAMES = ['Black', 'Red', 'Green', 'Yellow', 'Blue', 'Magenta', 'Cyan', 'White']
    MODE_NAMES = ['Foreground', 'Background', 'ForegroundBright', 'BackgroundBright']

    fmt = '{:11}' * len(COLOR_NAMES)
    print(' ' * 20 + fmt.format(*COLOR_NAMES))

    for mode_name in MODE_NAMES:
        print('{:20}'.format(mode_name), end='')
        for color_name in COLOR_NAMES:
            mode = getattr(Mode, mode_name)
            color = getattr(Color, color_name)
            print(tcolor(color, mode) + 'HelloColor' + treset(), end=' ')
        print()
