#!/usr/bin/env python3

import curses
from curses.textpad import Textbox
import sys
import os
import time
import argparse

parser = argparse.ArgumentParser('CSV Peek')
parser.add_argument('-f', '--file')
parser.add_argument('-c', '--columns', nargs='+')
parser.add_argument('-d', '--delimiter')

args = parser.parse_args(sys.argv[2:])

if args.delimiter:
    SEP = args.delimiter
else:
    SEP = '|'

if args.columns:
    filter_cols = args.columns
else:
    filter_cols = None
fpath = None
if args.file:
    fpath = args.file
if fpath is None and len(sys.argv) >= 2:
    fpath = sys.argv[1]
if fpath is None:
    raise Exception("filepath not supplied as argument")
    

PAGE_LINES = 30
PAGE_NUM = 0
PAGE_WIDTH = 80
PAGE_HSCROLL = 0

lines_read = 0

assert os.path.exists(fpath)
fin = open(fpath, 'r')

# stdscr = curses.initscr()
# curses.noecho()
# curses.cbreak()
# stdscr.keypad(1)

# def terminate():
    # curses.nocbreak()
    # stdscr.keypad(0)
    # curses.echo()
    # curses.endwin()

class Column():
    def __init__(self, name):
        self.name = name
        self.items = {}
        self.width = len(name)

    def add_item(self, line_num, item):
        item_width = len(item)
        if item_width > self.width:
            self.width = item_width
        self.items[line_num] = item


    def __str__(self):
        return "{} -- {} items".format(self.name, len(self.items))


def read_columns():
    fin.seek(0)
    cols = []
    header = fin.readline().strip().split(SEP)
    for col_name in header:
        col = Column(col_name)
        cols.append(col)
    return cols


columns = read_columns()


def read_up_to_line(n):
    global lines_read
    ct = 0
    while lines_read < n:
        ct += 1
        line = fin.readline().strip().split(SEP)
        for i, item in enumerate(line):
            columns[i].add_item(lines_read, item)
        lines_read += 1
    log("read to {}, count: {}".format(n, ct))


def filtered_columns():
    if filter_cols is None:
        return columns
    else:
        return [x for x in columns if x.name in filter_cols]

logging_enabled = False
logfile = None


def log(x):
    if not logging_enabled:
        return
    global logfile
    if logfile is None:
        logfile = open("peek_log.txt", "w")
    logfile.write("{}\n".format(x))


def main(stdscr):
    global PAGE_NUM, PAGE_HSCROLL, PAGW_WIDTH, PAGE_LINES
    max_yx = stdscr.getmaxyx()
    PAGE_LINES = max(5, max_yx[0] - 10)
    PAGE_WIDTH = max(20, max_yx[1] - 20)

    while True:
        stdscr.clear()
        start = PAGE_NUM * PAGE_LINES
        end = (PAGE_NUM + 1) * PAGE_LINES
        read_up_to_line(end)

        base = 3
        cols = filtered_columns()

        stdscr.addstr(0, 0, "press 'q' to quit, scroll left/right: '[' and ']', up/down: ',' and '.', jump to page: 'p'")
        stdscr.addstr(1, 0, "PAGE: {}, HSCROLL: {}, LINES: {} - {}".format(PAGE_NUM, PAGE_HSCROLL, start, end-1))

        horiz_start = PAGE_HSCROLL * PAGE_WIDTH
        horiz_end = (PAGE_HSCROLL + 1) * PAGE_WIDTH
        line_num_width = 10

        col_names = [x.name for x in cols]
        col_out = "{:>" + str(line_num_width) + "}"
        col_out = col_out.format("LineNum | ")
        for i, c in enumerate(col_names):
            width = columns[i].width
            col_out += "{:" + str(width) + "}" + " | "
            col_out = col_out.format(c)        
        stdscr.addstr(base, 0, col_out[horiz_start:horiz_end])

        stdscr.hline(base + 1, 0, "-", PAGE_WIDTH)
        at_end_of_file = False
        for i in range(start, end):
            y = (base + i + 2) - start
            out = ("[{:>" + str(line_num_width - 2) + "}]").format(i)
            for j, col in enumerate(cols):
                width = columns[j].width
                if width == 0:
                    continue    
                template = "{:" + str(width) + "}"
                #log("template: '{}'".format(template))
                try:
                    addition = template.format(col.items[i]) + " | "
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
        if cl == 'q': # QUTI
            break
        elif cl == '.': # page down
            PAGE_NUM += 1
        elif cl == ',' and PAGE_NUM > 0: # page up
            PAGE_NUM -= 1
        elif cl == ']': # page right
            PAGE_HSCROLL += 1
        elif cl == '[' and PAGE_HSCROLL > 0: # page left
            PAGE_HSCROLL -= 1
        elif cl == 'p':
            textbox(stdscr)


def textbox(win):
    global PAGE_NUM
    win.clear()
    prompt = "page number (hit Ctrl-G after typing number):"
    win.addstr(4, 4, prompt)
    tbox = Textbox(win)
    tbox.edit()
    raw_res = tbox.gather()
    res = raw_res.replace(prompt, '').strip()
    log("raw_res: '{}', res: '{}'".format(raw_res, res))
    new_page = convert_str_to_page_num(res)
    if new_page is not None:
        old = PAGE_NUM
        PAGE_NUM = new_page
        log('PAGE_NUM, old: {}, new: {} ({})'.format(old, PAGE_NUM, new_page))


def convert_str_to_page_num(s):
    try:
        n = int(s)        
    except Exception as e:
        log(e)
        return None
    if n < 0:
        log("can't convert pagenum: {}".format(n))
        return None
    return n



if __name__ == '__main__':
    curses.wrapper(main)
