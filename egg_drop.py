'''
A solver for the egg drop tech interview problem. The problem is that we have a building with
NUM_FLOORS floors, and we have NUM_EGGS eggs, and we need to determine the lowest floor from which
an egg will break if dropped. Any of the floors from 1, ..., NUM_FLOORS may or may not break the
egg, and we need to determine where the cutoff is. This is solved using the min_turn_mode setting of
SGSolver.
'''
from SGSolver import SGSolver

NUM_FLOORS = 100
NUM_EGGS = 3

print("Constructing egg drop instance with %d floors and %d eggs" % (NUM_FLOORS, NUM_EGGS))

gs = SGSolver()

def state_name (floors, eggs):
  return '%dF_%dE' % (floors, eggs)

# add states; variable 'xF_yE' corresponds to the state where you have x floors the breaking point
# might be in, and y eggs left
for floors in range(NUM_FLOORS+1):
  fixed_val = 0.0 if floors == 0 else None
  for eggs in range(1, NUM_EGGS+1):
    gs.add_state(state_name(floors, eggs), fixed_val)
gs.add_state(state_name(0, 0), 0.0)

# add moves
for floors in range(1, NUM_FLOORS+1):
  for eggs in range(1, NUM_EGGS+1):
    for i in range(1,floors+1):
      # if we have only 1 egg left, we have to do a linear search
      if eggs == 1 and i > 1:
        break
      prob = i * 1.0 / floors
      pstates = [(prob, state_name(i-1, eggs-1)),
                 (1-prob, state_name(floors-i, eggs))]
      #print(state_name(floors, eggs), pstates, 'floor %d' % i)
      gs.add_move(state_name(floors, eggs), pstates, 'floor %d' % i)

gs.min_turn_mode = True
gs.solve()

print("Expected number of moves: %.2f%%" % gs.winrate(state_name(NUM_FLOORS, NUM_EGGS)))
print("Best initial move: %s" % gs.bestmove(state_name(NUM_FLOORS, NUM_EGGS)))
