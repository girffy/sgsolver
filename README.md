The code in this repo began as a solver for a specific situation in poker, and then generalized into
a solver for what I'll call "stochastic games": games with finitely many states in which moves are
non-deterministic, and probabilistically produce a new game state. For a general writeup of the math
behind this (and an explanation of the poker scenario), see writeup.pdf.

`SGSolver.py` is the module that defines the SGSolver solver object that's used to instantiate and
solve problems. See `line.py`, `egg_drop.py`, and `poker.py` for increasingly complex examples of
how to use it.
