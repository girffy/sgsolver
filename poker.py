'''
The main motivating example for this repo. This file solves heads-up no-limit texas hold'em poker,
in the specific special case where your opponent always goes all-in immediately. A more detailed
write-up of how this is modelled (and the math behind it) can be found at writeup.pdf in this repo.
The short version is that, for each (k, blind, hand) triple representing our number of chips,
whether we're SB or BB, and what our 2-card hand is, we have a game state. And from each of these
states (where we don't have 0 or all the chips), we have two moves: call or fold.

For BUYIN = 100, this takes about 30 minutes to run on my machine.
'''
import pandas as pd
import numpy as np
import math
import datetime
from swiglpk import *

from SGSolver import SGSolver

# ---------- code for constructing the NLHE problem instance ----------
# the starting number of chips, as a multiple of the small blind (i.e., assuming small blind is 1).
# The most standard value is 100, though smaller values will help this run faster.
BUYIN = 100

print("Building problem with BUYIN=%s" % BUYIN)

# a bunch of code to build the hands variable, enumerating all hands up to equivalence, and their
# probabilities of being dealt.
df = pd.read_csv('probs.csv')
order = '23456789TJQKA'

def get_winrate(a, b, is_suited=False):
  a = a.upper()
  b = b.upper()

  if order.index(a) < order.index(b):
    a,b = b,a

  if is_suited:
    a,b = b,a

  return df[a][b] / 100.

def suited_winrate (a, b):
  return get_winrate(a, b, True)

def offsuit_winrate (a, b):
  return get_winrate(a, b, False)

def pair_winrate (a):
  return get_winrate(a, a, False)

# parse a standard format hand and produce its winrate
def hand_winrate (hstr):
  if len(hstr) == 2 and hstr[0] == hstr[1]:
    return pair_winrate (hstr[0])
  elif len(hstr) == 3 and hstr[2] == 'o':
    return offsuit_winrate (hstr[0], hstr[1])
  elif len(hstr) == 3 and hstr[2] == 's':
    return suited_winrate (hstr[0], hstr[1])
  else:
    raise Exception("Invalid hand: %s" % hstr)

# a list of hands, as (probability, hand string) pairs
hands = []

for c in order:
  hands.append(( (1/13. * 3/51.) , c+c))

for i, a in enumerate(order):
  for b in order[i+1:]:
    hands.append(( (2/13. * 1/51.) , b+a+'s'))
    hands.append(( (2/13. * 3/51.) , b+a+'o'))

amts = list(range(BUYIN*2+1))

def state_str (amt, blind, hand):
  return "%s_%s_%s" % (amt, blind, hand)

gs = SGSolver()

# add states
for amt in amts:
  for blind in "BB", "SB":
    gs.add_state(state_str(amt, blind, 'nohand'))
    for prob, hname in hands:
      fixed_val = None
      if amt == 0:
        fixed_val = 0.0
      elif amt == BUYIN*2:
        fixed_val = 1.0
      gs.add_state(state_str(amt, blind, hname), fixed_val)

# add moves
for amt in amts:
  for blind in "BB", "SB":
    # single compulsory move from nohand states, to 2-card hand states
    nohand_pstates = []
    for prob, hname in hands:
      nohand_pstates.append((prob, state_str(amt, blind, hname)))
    gs.add_move(state_str(amt, blind, 'nohand'), nohand_pstates, 'deal')

    # no moves from non-nohand states at 0 or BUYIN*2; game is over
    if amt == 0 or amt == BUYIN*2:
      continue

    for prob, hname in hands:
      state_name = state_str(amt, blind, hname)
      new_blind = "BB" if blind == "SB" else "SB"

      # call move
      winrate = hand_winrate(hname)
      call_win_amt = min(BUYIN*2, amt*2)
      call_lose_amt = max(0, 2*amt - 2*BUYIN)
      win_pstates = [(winrate, state_str(call_win_amt, new_blind, 'nohand')),
                     (1-winrate, state_str(call_lose_amt, new_blind, 'nohand'))]
      gs.add_move(state_name, win_pstates, "call")

      # fold move
      fold_amt = max(0, amt - (1 if blind == 'SB' else 2))
      fold_pstates = [(1, state_str(fold_amt, new_blind, 'nohand'))]
      gs.add_move(state_name, fold_pstates, "fold")

print("starting solve at " + datetime.datetime.now().strftime("%H:%M:%S"))
gs.solve()
print("finished at " + datetime.datetime.now().strftime("%H:%M:%S"))
print("winrate with $%s from SB/BB: %.2f%% / %.2f%%" %
  (BUYIN, gs.winrate('%s_SB_nohand' % BUYIN)*100, gs.winrate('%s_BB_nohand' % BUYIN)*100))
