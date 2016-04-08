"""Curses app for viewing CSV files."""


import argparse
import curses
from curses.textpad import Textbox
from datetime import datetime
import os


def parse_args():
    """Parse commandline arguments."""
    parser = argparse.ArgumentParser('CSV Peek')
    parser.add_argument('-f', '--input_file', required=True)
    parser.add_argument('-c', '--columns', nargs='+')
    parser.add_argument('-d', '--delimiter', default='|')
    parser.add_argument('-l', '--log_file')
    return parser.parse_args()


def log(x, log_file=None):
    if not log_file:
        return
    mode = 'a' if os.path.exists(log_file) else 'w'
    with open(log_file, mode=mode) as log:
        log.write("{}: {}\n".format(datetime.now(), x))


def process_page(page, delimiter, header, columns, widths):
    processed_page = []
    for line in page:
       values = line.split(delimiter)
       record = []
       for column in header:
           value = values[columns[column]]
           record.append(value)
           widths[column] = max(widths[column], len(value))
       processed_page.append(record)
    return processed_page


def peek(stdscr, input_file, delimiter, columns, log_file):
    base = 3
    line_num_width = 10
    page_hscroll = 0
    max_y, max_x = stdscr.getmaxyx()
    fin = open(input_file, encoding='utf-8')
    page_lines = max(5, max_y - 10)
    page_width = max(20, max_x - 20)
    page_num = 0
    page_buf = []
    header = fin.readline().strip().split(delimiter)
    if columns:
        _header = columns
        columns = dict((column, header.index(column)) for column in columns)
        header = _header
    else:
        columns = dict(zip(header, list(range(len(header)))))
    widths = dict((column, len(column)) for column in header)
    total_line_width = sum(widths.values())
    eof = False
    while True:
        stdscr.clear()
        while not eof and len(page_buf) <= page_num:
            next_page = []
            while not eof and len(next_page) < page_lines:
                try:
                    next_page.append(next(fin))
                except StopIteration:
                    eof = True
            if next_page:
                page_buf.append(next_page)
        if page_num >= len(page_buf):
            page_num = len(page_buf) - 1
        page = page_buf[page_num]
        if type(page[0]) is str:
            page = process_page(page, delimiter, header, columns, widths)
            page_buf[page_num] = page
            total_line_width = max(total_line_width, sum(widths.values()) + base * (len(widths) - 1) + line_num_width)
            max_hscroll = (total_line_width // (page_width - 1))
        page_len = len(page)
        start = page_num * page_lines
        end = start + min(page_lines, page_len)

        stdscr.addstr(0, 0, "press 'q' to quit, scroll left/right: '[' and ']', up/down: ',' and '.', jump to page: 'p'")
        stdscr.addstr(1, 0, "PAGE: {}, HSCROLL: {}, LINES: {} - {}".format(page_num, page_hscroll, start, end-1))

        horiz_start = page_hscroll * page_width
        horiz_end = (page_hscroll + 1) * page_width

        #col_names = [x.name for x in cols]
        col_out = "{:>" + str(line_num_width) + "}"
        col_out = col_out.format("LineNum | ")
        cells = []
        for col in header:
            width = str(widths[col])
            col_out += "{:" + width + "}" + " | "
            col_out = col_out.format(col)        
            cells.append("{:" + width + "}")
        stdscr.addstr(base, 0, col_out[horiz_start:horiz_end])
        template = ' | '.join(cells) + ' |'
        stdscr.hline(base + 1, 0, "-", page_width)
        for i in range(page_len):
            y = (base + i + 2)
            out = ("[{:>" + str(line_num_width - 2) + "}]").format(start + i)
            #log("template: '{}'".format(template))
            out += template.format(*page[i])
            #log("addition: '{}'".format(addition))
            stdscr.addstr(y, 0, out[horiz_start:horiz_end])

        stdscr.refresh()
        ch = stdscr.getkey()
        cl = ch.lower()
        if cl == 'q': # QUIT
            fin.close()
            break
        elif cl == '.': # page down
            page_num += 1
        elif cl == ',': # page up
            page_num = max(page_num - 1, 0)
        elif cl == ']': # page right
            page_hscroll = min(page_hscroll + 1, max_hscroll)
        elif cl == '[' and page_hscroll > 0: # page left
            page_hscroll = max(page_hscroll - 1, 0)
        elif cl == 'p':
            page_num = textbox(stdscr, page_num, log_file)


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
              'log_file': args.log_file}
    curses.wrapper(peek, **kwargs)


if __name__ == '__main__':
    main()

