import pandas as pd
import numpy as np
import math
import datetime
from swiglpk import *

EPSILON = 0.001

class State:
  def __init__ (self, name, fixed_val, col_idx):
    self.name = name
    self.fixed_val = fixed_val
    self.col_idx = col_idx
    self.moves = []

# basic struct to hold the state transitions and GLPK row index for a move
class Move:
  def __init__ (self, pstates, name, row_idx):
    self.name = name
    self.pstates = pstates
    self.row_idx = row_idx

class SGSolver:
  def __init__ (self):
    self.next_colidx = 1
    self.next_rowidx = 1
    self.total_nonzeros = 0
    self.lp = None

    # if True, the LP is formulated such that each primal variable, instead of representing the
    # winrate from the given state, minimizes the expected number of turns starting at that state,
    # before ending up in a terminal state.
    self.min_turn_mode = False

    # a mapping of state names to State objects
    self.states = {}

    # maps a state to a list of its moves
    self.statemoves = {}

  # adds a state to the LP. If a fixed_val is supplied, this state is terminal, and has a winrate of
  # fixed_val (usually 0 or 1)
  def add_state (self, state_name, fixed_val = None):
    assert type(state_name) == str
    assert state_name not in self.states
    self.states[state_name] = State(state_name, fixed_val, self.next_colidx)
    self.next_colidx += 1

  # given a state and a move, add the move to the game. A move is specified as a list of (p, state)
  # pairs, indicating the states that this move can result in, along with each of their
  # probabilities p
  def add_move (self, state_name, pstates, move_name = None):
    assert state_name in self.states
    state = self.states[state_name]
    total_prob = sum([p for p, state2 in pstates])
    assert abs(total_prob - 1) < EPSILON

    for p, state2 in pstates:
      if state2 not in self.states:
        raise Exception ("add_move: Unknown state: %s" % state2)

    move = Move(pstates, move_name, self.next_rowidx)
    self.next_rowidx += 1

    self.total_nonzeros += 1 + len(pstates)

    state.moves.append(move)

  # create a GPLK lp object out of the current states and moves
  def create_lp (self):
    ia = intArray(1+self.total_nonzeros)
    ja = intArray(1+self.total_nonzeros)
    ar = doubleArray(1+self.total_nonzeros)

    lp = glp_create_prob()
    glp_set_prob_name(lp, "SGSolver LP");
    glp_set_obj_dir(lp, GLP_MAX if self.min_turn_mode else GLP_MIN);
    glp_add_cols(lp, self.next_colidx)
    glp_add_rows(lp, self.next_rowidx)

    # initialize columns
    for name, state in self.states.items():
      glp_set_col_name(lp, state.col_idx, 'state(%s)' % state.name)
      if state.fixed_val == None:
        glp_set_col_bnds(lp, state.col_idx, GLP_LO, 0.0, 0.0)
        glp_set_obj_coef(lp, state.col_idx, 1.0)
      else:
        glp_set_col_bnds(lp, state.col_idx, GLP_FX, state.fixed_val, state.fixed_val)

    # initialize rows
    ar_idx = 0
    for state_idx, state in enumerate(self.states.values()):
      for move_idx, move in enumerate(state.moves):
        glp_set_row_name(lp, move.row_idx, "move(%s,%s)" % (state.name, move.name))
        if self.min_turn_mode:
          glp_set_row_bnds(lp, move.row_idx, GLP_UP, 1.0, 1.0)
        else:
          glp_set_row_bnds(lp, move.row_idx, GLP_LO, 0.0, 0.0)

        ar_idx += 1
        ia[ar_idx] = move.row_idx
        ja[ar_idx] = state.col_idx
        ar[ar_idx] = 1.0

        for prob, state2 in move.pstates:
          ar_idx += 1
          ia[ar_idx] = move.row_idx
          ja[ar_idx] = self.states[state2].col_idx
          ar[ar_idx] = -prob

    glp_load_matrix(lp, ar_idx, ia, ja, ar)
    self.lp = lp
    return lp

  # create the GLPK lp object, and solve the problem
  def solve (self):
    lp = self.create_lp()
    glp_simplex(lp, None)
    return lp

  # get the winrate of a given state
  def winrate (self, state_name):
    assert self.lp != None
    assert state_name in self.states
    return glp_get_col_prim(self.lp, self.states[state_name].col_idx)

  # get the winrate of a move
  def move_winrate (self, move):
    val = 0
    for p, state in move.pstates:
      val += p * self.winrate(state)
    return val

  # get the optimal move from a given state
  def bestmove (self, state_name):
    assert self.lp != None
    assert state_name in self.states
    assert len(self.states[state_name].moves) > 0
    best_move = max(self.states[state_name].moves,
      key = lambda mv: glp_get_row_stat(self.lp, mv.row_idx))
    return best_move.name

  # debug function, outlining the moves usable from a state and their values
  def show_moves (self, state_name):
    assert self.lp != None
    assert state_name in self.states
    state = self.states[state_name]
    print("State: %s (val=%.3f)" % (state_name, self.winrate(state_name)))
    for move in state.moves:
      print("  move: %s (val=%.3f)" % (move.name, self.move_winrate(move)))
      for p, state in sorted(move.pstates, key = lambda x: x[0]):
        val = p * self.winrate(state)
        print("    %s (%.2f%%): %.3f (wtd: %.3f)" % (state, p*100, self.winrate(state), val))
