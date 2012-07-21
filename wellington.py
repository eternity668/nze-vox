#!/usr/bin/python

import re
from collections import namedtuple

def utterance_generator(f):
    utt = []
    uid = None
    for line in f:
        line = line.strip()
        if line[:5] == '<WSC#': #new utterance
            if uid:
                yield (uid, ' '.join(utt))
            utt = []
            uid = line[5:-1]
        elif line in ('<I>', '</I>'):
            pass
        else:
            utt.append(line)


def entaggen(s):
    return '++' + s + '++', None

def time_or_comment(s):
    m = re.match('^(\d+):(\d\d)$', s)
    if m:
        minutes, seconds = m.group(1, 2)
        return '', {'time': int(minutes) + float(seconds) / 60.}
    return '', None

def echo(s):
    return s, None

def drop(s):
    return '', None

Tag = namedtuple('tag', ['tag', 'solitary', 'ignore', 'filter'])
TAG_DATA = [
    [",",   True,    False,   echo],
    [".",   False,   False,   entaggen],
    ["[",   False,   False,   echo],
    ["{",   False,   True,    echo],
    ["&",   False,   False,   time_or_comment],
    ["I",   False,   True,    echo],
    ["laughs", False, False,  echo],
    ["O",   False,   False,   entaggen],
]
TAG_MAP = {x[0]: Tag(*x) for x in TAG_DATA}

ENTAGGEN_WORDS = {
    'er': '++ER++',
    'um': '++UM++',
}

def comment_parser(g):
    entaggen_word = ENTAGGEN_WORDS.get
    for uid, utt in g:
        ubits = utt.split('<')
        done = [entaggen_word(w, w) for w in ubits[0].split()]
        stack = []
        timepoints = []
        for bit in ubits[1:]:
            tag, content = bit.split('>', 1)
            if tag[0] != '/':
                #opening or single tag
                t = TAG_MAP[tag]
                if not t.ignore and not t.solitary:
                    stack.append(t)
                filter = t.filter
            else:
                tag = tag[1:]
                if TAG_MAP[tag].ignore:
                    continue
                if not stack or stack[-1].tag != tag:
                    raise TabError("found </%s> but stack is %s"
                                   % (tag, stack))
                stack.pop()
                if stack:
                    filter = stack[-1].filter
                else:
                    filter = echo

            text, meta = filter(content)
            words = text.split()
            if meta and 'time' in meta:
                timepoints.append((meta['time'], len(done), len(' '.join(done))))

            done.extend(entaggen_word(w, w) for w in words)

        yield uid, ' '.join(done), timepoints


def main():
    f = open('corpora/wellington/DGI038.TXT')
    g = utterance_generator(f)
    h = comment_parser(g)
    for uid, utt, timepoints in h:
        print uid, utt, timepoints

main()
