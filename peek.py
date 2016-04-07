"""Curses app for viewing CSV files."""


print("Importing libraries...")


import argparse
import csv
import curses
from curses.textpad import Textbox
from datetime import datetime
import os
import pandas as pd


def parse_args():
    """Parse commandline arguments."""
    parser = argparse.ArgumentParser('CSV Peek')
    parser.add_argument('-f', '--input_file', required=True)
    parser.add_argument('-c', '--columns', nargs='+')
    parser.add_argument('-d', '--delimiter', default='|')
    parser.add_argument('-l', '--log_file')
    parser.add_argument('--page_width', type=int, default=80)
    parser.add_argument('--page_lines', type=int, default=30)
    return parser.parse_args()


def log(x, log_file=None):
    if not log_file:
        return
    mode = 'a' if os.path.exists(log_file) else 'w'
    with open(log_file, mode=mode) as log:
        log.write("{}: {}\n".format(datetime.now(), x))


def peek(stdscr, input_file, delimiter, columns, page_width, page_lines, log_file):
    page_hscroll = 0
    max_y, max_x = stdscr.getmaxyx()
    page_lines = max(5, max_y - 10)
    page_width = max(20, max_x - 20)

    page_num = 0
    reader = pd.read_csv(input_file, encoding='utf-8', dtype=str, delimiter=delimiter, quoting=csv.QUOTE_NONE, na_filter=False, usecols=columns, chunksize=page_lines)
    page_buf = []
    widths = dict()
    page_lens = []
    ordered_header = []
    while True:
        stdscr.clear()
        while len(page_buf) < page_num + 1:
            try:
                page_len = 0
                if not ordered_header:
                    first_page = next(reader)
                    ordered_header = list(first_page.columns)
                    next_page = first_page.to_dict(orient='list')
                else:
                    next_page = next(reader).to_dict(orient='list')
                for column in next_page:
                    if not page_len:
                        page_len = len(next_page[column])
                    width = widths.get(column, len(column))
                    widths[column] = max(*[len(value) for value in next_page[column]], width)
                page_buf.append(next_page)
                page_lens.append(page_len)
            except StopIteration:
                page_num = len(page_buf) - 1
        page = page_buf[page_num]
        start = page_num * page_lines
        end = start + min(page_lines, page_lens[page_num])
        base = 3

        stdscr.addstr(0, 0, "press 'q' to quit, scroll left/right: '[' and ']', up/down: ',' and '.', jump to page: 'p'")
        stdscr.addstr(1, 0, "PAGE: {}, HSCROLL: {}, LINES: {} - {}".format(page_num, page_hscroll, start, end-1))

        horiz_start = page_hscroll * page_width
        horiz_end = (page_hscroll + 1) * page_width
        line_num_width = 10

        #col_names = [x.name for x in cols]
        col_out = "{:>" + str(line_num_width) + "}"
        col_out = col_out.format("LineNum | ")
        for col in ordered_header:
            width = str(widths[col])
            col_out += "{:" + width + "}" + " | "
            col_out = col_out.format(col)        
        stdscr.addstr(base, 0, col_out[horiz_start:horiz_end])

        stdscr.hline(base + 1, 0, "-", page_width)
        at_end_of_file = False
        for i in range(page_lens[page_num]):
            y = (base + i + 2)
            out = ("[{:>" + str(line_num_width - 2) + "}]").format(start + i)
            for col in ordered_header:
                width = widths[col]
                template = "{:" + str(width) + "}"
                #log("template: '{}'".format(template))
                try:
                    addition = template.format(page[col][i]) + " | "
                except KeyError:
                    at_end_of_file = True
                    break
                #log("addition: '{}'".format(addition))
                out += addition
            if at_end_of_file:
                break
            out = out[horiz_start:horiz_end]
            stdscr.addstr(y, 0, out)

        stdscr.refresh()
        ch = stdscr.getkey()
        cl = ch.lower()
        if cl == 'q': # QUIT
            break
        elif cl == '.': # page down
            page_num += 1
        elif cl == ',' and page_num > 0: # page up
            page_num -= 1
        elif cl == ']': # page right
            page_hscroll += 1
        elif cl == '[' and page_hscroll > 0: # page left
            page_hscroll -= 1
        elif cl == 'p':
            page_num = textbox(stdscr, page_num)


def textbox(win, page_num, log_file=None):
    win.clear()
    prompt = "page number (hit Ctrl-G after typing number):"
    win.addstr(4, 4, prompt)
    tbox = Textbox(win)
    tbox.edit()
    raw_res = tbox.gather()
    res = raw_res.replace(prompt, '').strip()
    log("raw_res: '{}', res: '{}'".format(raw_res, res), log_file)
    new_page = convert_str_to_page_num(res, log_file)
    if new_page is not None:
        old = page_num
        page_num = new_page
        log('PAGE_NUM, old: {}, new: {} ({})'.format(old, page_num, new_page), log_file)
    return page_num


def convert_str_to_page_num(s, log_file):
    try:
        n = int(s)        
        assert n >= 0, 'page_num less than 0'
        return n
    except Exception as e:
        log(e, log_file)
        return None


def main():
    """Parse commandline arguments & call peek."""
    args = parse_args()
    kwargs = {'input_file': args.input_file,
              'delimiter': args.delimiter,
              'columns': args.columns,
              'page_width': args.page_width,
              'page_lines': args.page_lines,
              'log_file': args.log_file}
    curses.wrapper(peek, **kwargs)


if __name__ == '__main__':
    main()

