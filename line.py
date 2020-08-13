'''
A very simple game, which serves as a simple example of how to use the solver.  This is played on a
line with LINE_SIZE squares. The goal is to reach the leftmost square (0), and you lose if you reach
the rightmost square. Each round, you can choose a direction to go; with probability SUCCESS_RATE,
you move 1 in that direction, otherwise you move in the opposite direction. Of course, the optimal
strategy is to always move left.
'''
from SGSolver import SGSolver

LINE_SIZE = 10
SUCCESS_RATE = 0.66667

gs = SGSolver()
for i in range(LINE_SIZE):
  fixed_val = None
  if i == 0:
    fixed_val = 1
  elif i == LINE_SIZE-1:
    fixed_val = 0
  gs.add_state(str(i), fixed_val)

for i in range(1, LINE_SIZE-1):
  for dirn in [-1, 1]:
    pstates = [(SUCCESS_RATE, str(i+dirn)),  (1-SUCCESS_RATE, str(i-dirn))]
    gs.add_move(str(i), pstates, 'move %s' % ('left' if dirn == -1 else 'right'))

gs.solve()
print("winrates:")
for i in range(LINE_SIZE):
  bm_str = "" if i in [0, LINE_SIZE-1] else ("(best move: %s)" % gs.bestmove(str(i)))
  print("From state %d: %.2f%% %s" % (i, gs.winrate(str(i))*100, bm_str))
