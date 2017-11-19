#!/usr/bin/python

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import argparse
import functools
import os
import re
import sys
import time

from future.builtins import range  # pylint: disable=redefined-builtin
import numpy as np
import pygame


SHAPES = {
    "diehard": [
        [0, 0, 0, 0, 0, 0, 1, 0],
        [1, 1, 0, 0, 0, 0, 0, 0],
        [0, 1, 0, 0, 0, 1, 1, 1],
    ],
    "boat": [
        [1, 1, 0],
        [1, 0, 1],
        [0, 1, 0],
    ],
    "r_pentomino": [
        [0, 1, 1],
        [1, 1, 0],
        [0, 1, 0],
    ],
    "beacon": [
        [0, 0, 1, 1],
        [0, 0, 1, 1],
        [1, 1, 0, 0],
        [1, 1, 0, 0],
    ],
    "acorn": [
        [0, 1, 0, 0, 0, 0, 0],
        [0, 0, 0, 1, 0, 0, 0],
        [1, 1, 0, 0, 1, 1, 1],
    ],
    "spaceship": [
        [0, 0, 1, 1, 0],
        [1, 1, 0, 1, 1],
        [1, 1, 1, 1, 0],
        [0, 1, 1, 0, 0],
    ],
    "block_switch_engine": [
        [0, 0, 0, 0, 0, 0, 1, 0],
        [0, 0, 0, 0, 1, 0, 1, 1],
        [0, 0, 0, 0, 1, 0, 1, 0],
        [0, 0, 0, 0, 1, 0, 0, 0],
        [0, 0, 1, 0, 0, 0, 0, 0],
        [1, 0, 1, 0, 0, 0, 0, 0],
    ],
    "five_by_five": [
        [1, 1, 1, 0, 1],
        [1, 0, 0, 0, 0],
        [0, 0, 0, 1, 1],
        [0, 1, 1, 0, 1],
        [1, 0, 1, 0, 1],
    ],
    "narrow": [
        [1,1,1,1,1,1,1,1,0,1,1,1,1,1,0,0,0,1,1,1,0,0,0,0,0,0,1,1,1,1,1,1,1,0,1,1,1,1,1]
    ],
    "glider_gun": [
        [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0],
        [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,1,0,0,0,0,0,0,0,0,0,0,0],
        [0,0,0,0,0,0,0,0,0,0,0,0,1,1,0,0,0,0,0,0,1,1,0,0,0,0,0,0,0,0,0,0,0,0,1,1],
        [0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,1,0,0,0,0,1,1,0,0,0,0,0,0,0,0,0,0,0,0,1,1],
        [1,1,0,0,0,0,0,0,0,0,1,0,0,0,0,0,1,0,0,0,1,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
        [1,1,0,0,0,0,0,0,0,0,1,0,0,0,1,0,1,1,0,0,0,0,1,0,1,0,0,0,0,0,0,0,0,0,0,0],
        [0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,1,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0],
        [0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
        [0,0,0,0,0,0,0,0,0,0,0,0,1,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    ],
}


NEIGHBORS = np.array([
    [-1, -1], [-1, 0], [-1, 1],
    [ 0, -1],          [ 0, 1],
    [ 1, -1], [ 1, 0], [ 1, 1],
])


def update_rules(rules, state):
  """A general rules implementation."""
  count = sum(np.roll(state, n, (0, 1)) for n in NEIGHBORS)
  return rules[state.flatten(), count.flatten()].reshape(state.shape)


def update_b3s23(state):
  """A faster implementation for the usual case."""
  count = sum(np.roll(state, n, (0, 1)) for n in NEIGHBORS)
  return (count == 3) | (state & (count == 2))


def draw(window, state):
  raw_surface = pygame.surfarray.make_surface(state * 255)
  pygame.transform.scale(raw_surface, window.get_size(), window)
  pygame.display.update()


def rand_state(size, fraction):
  state = np.zeros(size, dtype=np.uint8)
  state[np.random.rand(*size) < fraction] = 1
  return state


def shape(size, name):
  state = np.zeros(size, dtype=np.uint8)
  arr = np.array(SHAPES[name], dtype=np.uint8)
  loc = (size + np.array(arr.shape)) // 2
  state[loc[0]:loc[0]+arr.shape[0], 
        loc[1]:loc[1]+arr.shape[1]] = arr
  return state


def parse_rules(rule_str):
  m = re.match("^b(\d*)/?s(\d*)$", rule_str, re.IGNORECASE)
  if not m:
    sys.exit("Bad rules string. Format: b\d*s\d*")
  bs, ss = m.groups()
  bs = {int(a) for a in list(bs) if 0 < int(a) < 9}
  ss = {int(a) for a in list(ss) if 0 < int(a) < 9}
  if bs == {3} and ss == {2, 3}:
    return update_b3s23
  else:
    rules = np.zeros((2, 9), dtype=np.uint8)
    for b in bs:
      rules[0][int(b)] = 1
    for s in ss:
      rules[1][int(s)] = 1
    print("Rules: Born: %s, Survive: %s" % (rules[0], rules[1]))
    return functools.partial(update_rules, rules)


def main():
  parser = argparse.ArgumentParser(description='Game of life!')
  parser.add_argument('--shape', default=None, choices=sorted(SHAPES.keys()))
  parser.add_argument('--rules', default="b3/s23", help='Rules in b3/s23 format')
  parser.add_argument('--px_size', default=2, type=int, help='Pixel size')
  parser.add_argument('--steps', default=1000000000, type=int, help='Steps before exiting')
  parser.add_argument('--skip', default=1, type=int, help='Steps between rendering')
  parser.add_argument('--fps', default=100, type=float, help='Max fps')
  parser.add_argument('--start_rand', default=0.1, type=float, help='Noise per step')
  parser.add_argument('--noise', default=0, type=float, help='Noise per step')
  parser.add_argument('--no_reset', action='store_true', help="Continue even if it's stabilized.")
  parser.add_argument('--no_periodic', action='store_true', help="Disable periodic boundaries.")
  parser.add_argument('--window_fraction', type=float, default=0.75,
                      help='How big should the window be relative to resolution.')
  args = parser.parse_args()

  update = parse_rules(args.rules)

  pygame.init()
  display_info = pygame.display.Info()
  display_size = np.array([display_info.current_w, display_info.current_h])
  window_size = (display_size * args.window_fraction).astype(np.int32)
  window = pygame.display.set_mode(window_size, 0, 8)
  pygame.display.set_caption("Game of Life")

  grid = window_size.transpose() // args.px_size
  print("grid:", grid)
  if args.shape:
    state = shape(grid, args.shape)
  else:
    state = rand_state(grid, args.start_rand)

  try:
    history = set()
    start = time.time()
    for step in range(args.steps):
      step_start_time = time.time()
      if step % args.skip == 0:
        draw(window, state)
      state = update(state)
      if args.noise:
        state += (np.random.rand(*grid) < args.noise).astype(dtype=np.uint8)
      if args.no_periodic:
        state[-1, :] = 0
        state[:, -1] = 0
      if not args.no_reset:
        h = hash(state.tostring())
        if h in history:
          state = rand_state(grid, args.start_rand)
          history.clear()
        else:
          history.add(h)
      for event in pygame.event.get():
        if event.type == pygame.QUIT:
          return
        elif event.type == pygame.KEYDOWN:
          if event.key in (pygame.K_ESCAPE, pygame.K_F4):
            return
          elif event.key in (pygame.K_PAGEUP, pygame.K_PAGEDOWN):
            if pygame.key.get_mods() & pygame.KMOD_CTRL:
              if event.key == pygame.K_PAGEUP:
                args.skip += 1
              elif args.skip > 1:
                args.skip -= 1
              print("New skip:", args.skip)
            else:
              args.fps *= 1.25 if event.key == pygame.K_PAGEUP else 1 / 1.25
              print("New max fps: %.1f" % args.fps)
      elapsed_time = time.time() - step_start_time
      time.sleep(max(0, 1 / args.fps - elapsed_time))
  except KeyboardInterrupt:
    pass
  finally:
    elapsed = time.time() - start
    print("Ran %s steps in %0.3f seconds: %.0f steps/second" % (step, elapsed, step / elapsed))


if __name__ == "__main__":
  main()
