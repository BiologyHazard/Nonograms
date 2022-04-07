from io import TextIOWrapper
import numpy as np
import time

UNKNOWN = 0
BLACK = 1
WHITE = 2

print_chars = {
    UNKNOWN: '🟨',
    BLACK: '⬛',
    WHITE: '⬜'
}


def solve_one_line(line, hint):
    def can_insert_color(idx, x, color):  # 从idx开始的x格插入color不冲突
        if idx + x > line_size:
            return False
        for i in range(idx, idx + x):
            if line[i] != UNKNOWN and line[i] != color:
                return False
        return True

    def can_fill(idx, group):  # 从 第idx个格子, 第group组黑块 开始的子问题 是否有解
        if calc[idx][group] != 0:
            return bool(calc[idx][group] - 1)

        black_num = hint[group]  # 该组黑块个数
        ans = False

        if group == group_size - 1:  # 如果是最后一组
            if (can_insert_color(idx, black_num, BLACK) and
                    can_insert_color(idx + black_num,
                                     line_size - idx - black_num, WHITE)):
                ans = True
                can_place_black[idx:idx + black_num] = True  # 可以插入黑色
                can_place_white[idx + black_num:line_size] = True  # 后面的都可以插入白色

        else:  # 如果不是最后一组
            if (can_insert_color(idx, black_num, BLACK) and  # 先插入这些黑色
                    can_insert_color(idx + black_num, 1, WHITE) and  # 再插入一个白色
                    can_fill(idx + black_num + 1, group + 1)):  # 递归调用，后面的子问题有解
                ans = True
                can_place_black[idx:idx + black_num] = True
                can_place_white[idx + black_num] = True

        if (can_insert_color(idx, 1, WHITE) and  # 如果第idx格可以插入白色
                can_fill(idx + 1, group)):  # 如果后面的子问题有解
            ans = True
            can_place_white[idx] = True

        calc[idx][group] = int(ans) + 1
        return ans

    line_size = len(line)
    group_size = len(hint)
    can_place_white = np.zeros(line_size, dtype=np.bool_)
    can_place_black = np.zeros(line_size, dtype=np.bool_)
    calc = np.zeros((line_size + 1, group_size), dtype=np.int8)
    can_fill(0, 0)
    result = np.empty(line_size, dtype=np.int8)
    solved = True
    for i in range(line_size):
        if can_place_white[i] and can_place_black[i]:
            result[i] = UNKNOWN
            solved = False
        elif can_place_black[i]:
            result[i] = BLACK
        elif can_place_white[i]:
            result[i] = WHITE
        else:
            return None
    return result, solved


def solve(map, height, width, x_hints, y_hints, solved_x, solved_y, logf=None):
    condition_changed = True
    while condition_changed:
        condition_changed = False

        for i in range(height):
            if not solved_x[i]:
                line = map[i].copy()
                hint = x_hints[i]
                line_solved, solved = solve_one_line(line, hint)
                if not (line == line_solved).all():  # line与line_solved有任一值不等
                    condition_changed = True
                    map[i] = line_solved
                    logf.write(
                        f'row {i} (hint:{hint}) from {print_line(line)} to {print_line(line_solved)}\n')
                    if solved:
                        solved_x[i] = True

        for line in map:
            logf.write(print_line(line) + '\n')
        logf.write('\n')

        for i in range(width):
            if not solved_y[i]:
                line = map[..., i].copy()
                hint = y_hints[i]
                line_solved, solved = solve_one_line(line, hint)
                if not (line == line_solved).all():  # line与line_solved有任一值不等
                    condition_changed = True
                    map[..., i] = line_solved
                    logf.write(
                        f'col {i} (hint:{hint}) from {print_line(line)} to {print_line(line_solved)}\n')
                    if solved:
                        solved_y[i] = True

        for line in map:
            logf.write(print_line(line) + '\n')
        logf.write('\n\n')
    return map


def print_line(line, print_chars=print_chars):
    l = []
    for i in line:
        l.append(print_chars[i])
    return ''.join(l)


class Nonograms:
    def __init__(self, file=None, height=None, width=None, x_hints=None, y_hints=None):
        if file is not None:
            if isinstance(file, str):
                with open(file, 'r', encoding='utf-8') as f:
                    self.load_from_file(f)
            elif isinstance(file, TextIOWrapper):
                self.load_from_file(file)
            else:
                raise TypeError
        else:
            self.init_game(height, width, x_hints, y_hints)

    # def __len__(self):
    #     return self.height * self.width

    def load_from_file(self, map_file: TextIOWrapper):
        hints = map_file.readlines()
        hints = [hint.strip() for hint in hints if len(hint.strip()) > 0]
        for i, hint in enumerate(hints):
            if hint.startswith('-') or hint.startswith('*'):
                self.height = i
                self.width = len(hints) - i - 1
        self.map = np.empty((self.height, self.width), dtype=np.int8)
        self.map.fill(UNKNOWN)
        x_hint = hints[:self.height]
        self.x_hints = [[int(x) for x in hint.split()] for hint in x_hint]
        y_hint = hints[self.height + 1:]
        self.y_hints = [[int(x) for x in hint.split()] for hint in y_hint]

    def init_game(self, height=None, width=None, x_hints=None, y_hints=None):
        self.height = height
        self.width = width
        self.map = np.empty((height, width), dtype=np.int8)
        self.map.fill(UNKNOWN)
        self.x_hints = x_hints
        self.y_hints = y_hints
        if (len(self.x_hints) != self.height) or (len(self.y_hints) != self.width):
            raise ValueError

    def get_row(self, x):
        return self.map[x]

    def get_col(self, y):
        return self.map[..., y]

    def print(self, print_chars=print_chars):
        for line in self.map:
            print(print_line(line))

    def solve(self, logf=None):
        self.map = solve(self.map,
                         self.height,
                         self.width,
                         self.x_hints,
                         self.y_hints,
                         np.zeros(self.height, dtype=np.int8),
                         np.zeros(self.width, dtype=np.int8),
                         logf)
        return self.map


if __name__ == '__main__':
    time0 = time.time()
    with open('solve.log', 'w', encoding='utf-8') as logf:
        # print(solve_one_line(np.array([0, 0, 1, 0, 0, 0, 0, 0, 0, 0]), [4]))
        nonograms = Nonograms('game_map.txt')
        nonograms.solve(logf)
        nonograms.print()
        # print(solve_one_line(np.array([0, 0, 1, 1, 0]), [3]))
        # print(solve_one_line(np.zeros(50, np.int8), [3, 4, 1, 6, 1, 3, 2, 12, 1]))
    print(f'time used {time.time() - time0:.3f}s')
