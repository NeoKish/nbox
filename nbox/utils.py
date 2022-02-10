############################################################
# This file is d0 meaning that this has no dependencies!
# Do not import anything from rest of nbox here! 
############################################################

# this file has bunch of functions that are used everywhere

import os
import io
import hashlib
import requests
import tempfile
import randomname
from uuid import uuid4
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed, wait


# logging/

import logging
logger = logging.getLogger()

# /logging

# common/

nbox_session = requests.Session()

import grpc
from .hyperloop.nbox_ws_pb2_grpc import WSJobServiceStub

channel = grpc.insecure_channel("[::]:50051")
nbx_stub = WSJobServiceStub(channel)

# /common

# lazy_loading/

def isthere(*packages, soft = True):
  def wrapper(fn):
    def _fn(*args, **kwargs):
      # since we are lazy evaluating this thing, we are checking when the function
      # is actually called. This allows checks not to happen during __init__.
      for package in packages:
        try:
          __import__(package)
        except ImportError:
          if not soft:
            raise Exception(f"{package} is not installed")
          # raise a warning, let the modulenotfound exception bubble up
          logger.warning(
            f"{package} is not installed, but is required by {fn.__module__}, some functionality may not work"
          )
      return fn(*args, **kwargs)
    return _fn
  return wrapper

def _isthere(*packages):
  for package in packages:
    try:
      __import__(package)
    except Exception:
      return False
  return True

# /lazy_loading

# file path/reading

def get_files_in_folder(folder, ext = [".txt"]):
  # this method is faster than glob
  import os
  all_paths = []
  for root,_,files in os.walk(folder):
    for f in files:
      for e in ext:
        if f.endswith(e):
          all_paths.append(os.path.join(root,f))
  return all_paths

def fetch(url, force = False):
  # efficient loading of URLs
  fp = join(tempfile.gettempdir(), hash_(url))
  if os.path.isfile(fp) and os.stat(fp).st_size > 0 and not force:
    with open(fp, "rb") as f:
      dat = f.read()
  else:
    dat = requests.get(url).content
    with open(fp + ".tmp", "wb") as f:
      f.write(dat)
    os.rename(fp + ".tmp", fp)
  return dat

def folder(x):
  # get the folder of this file path
  return os.path.split(os.path.abspath(x))[0]

def join(x, *args):
  return os.path.join(x, *args)

NBOX_HOME_DIR = join(os.path.expanduser("~"), ".nbx")

# /path

# misc/

def get_random_name(uuid = False):
  if uuid:
    return str(uuid4())
  return randomname.generate()

def hash_(item, fn="md5"):
  return getattr(hashlib, fn)(str(item).encode("utf-8")).hexdigest()

# /misc

# model/

@isthere("PIL", soft = False)
def get_image(file_path_or_url):
  from PIL import Image
  if os.path.exists(file_path_or_url):
    return Image.open(file_path_or_url)
  else:
    return Image.open(io.BytesIO(fetch(file_path_or_url)))

def convert_to_list(x):
  # recursively convert tensors -> list
  import torch
  if isinstance(x, list):
    return x
  if isinstance(x, dict):
    return {k: convert_to_list(v) for k, v in x.items()}
  elif isinstance(x, (torch.Tensor, np.ndarray)):
    x = np.nan_to_num(x, -1.42069)
    return x.tolist()
  else:
    raise Exception("Unknown type: {}".format(type(x)))

# /model


################################################################################
# Parallel
# ========
# There already are many multiprocessing libraries for thread, core, pod, cluster
# but thee classes below are inspired by https://en.wikipedia.org/wiki/Collective_operation
#
# And that is why they are blocking classes, ie. it won't stop till all the tasks
# are completed. For reference please open the link above which has diagrams, there
# nodes can just be threads/cores/... Here is description for each of them:
#
# - Pool: apply same functions on different inputs
# - Branch: apply different functions on different inputs
################################################################################

# pool/

class PoolBranch:
  def __init__(self, mode = "thread", max_workers = 2, _name: str = get_random_name(True)):
    """Threading is hard, your brain is not wired to handle parallelism. You are a blocking
    python program. So a blocking function for you.

    Args:
      mode (str, optional): There can be multiple pooling strategies across cores, threads,
        k8s, nbx-instances etc.
      max_workers (int, optional): Numbers of workers to use
      _name (str, optional): Name of the pool, used for logging

    Usage:
      
      fn = [
        lambda x : x + 0,
        lambda x : x + 1,
        lambda x : x + 2,
        lambda x : x + 3,
      ]

      args = [
        (1,), (2,), (3,), (4,),
      ]

      pool = PoolBranch()
      out = pool(fn[2], *args)
      # [1+2, 2+2, 3+2, 4+2] => [3, 4, 5, 6]
      print(out)

      branch = PoolBranch()
      out = branch(fn, *args)
      # [1+0, 2+1, 3+2, 4+3] => [1, 3, 5, 7]
      print(out)
    """
    self.mode = mode
    self.item_id = -1 # because +1 later
    self.futures = {}

    if mode == "thread":
      self.executor = ThreadPoolExecutor(
        max_workers=max_workers,
        thread_name_prefix=_name
      )
    elif mode == "process":
      self.executor = ProcessPoolExecutor(
        max_workers=max_workers,
      )
    else:
      raise Exception(f"Only 'thread/process' modes are supported")
    logger.info(f"Starting {mode.upper()}-PoolBranch ({_name}) with {max_workers} workers")

  def __call__(self, fn, *args):
    """Run any function ``fn`` in parallel, where each argument is a list of arguments to
    pass to ``fn``. Result is returned in the **same order as the input**.

      ..code-block
      
        if fn is callable:
          thread(fn, a) for a in args -> list of results
        elif fn is list and fn[0] is callable:
          thread(_fn, a) for _fn, a in (fn args) -> list of results
    """
    assert isinstance(args[0], (tuple, list))
    
    futures = {}
    if isinstance(fn, (list, tuple)) and callable(fn[0]):
      assert len(fn) == len(args), f"Number of functions ({len(fn)}) and arguments ({len(args)}) must be same in branching"
    else:
      assert callable(fn), "fn must be callable in pooling"
      fn = [fn for _ in range(len(args))] # convinience

    self.item_id += len(futures)
    results = {}
    
    if self.mode == "thread":
      for i, (_fn, x) in enumerate(zip(fn, args)):
        futures[self.executor.submit(_fn, *x)] = i # insertion index
      for future in as_completed(futures):
        try:
          result = future.result()
          results[futures[future]] = result # update that index
        except Exception as e:
          logger.error(f"{self.mode} error: {e}")
          raise e

      res = [results[x] for x in range(len(results))]
    
    elif self.mode == "process":
      res = {}
      for i in range(len(args)):
        # print(args[i],)
        out = self.executor.submit(
          fn[i], args[i],
        )
        res[out] = i
        # print(out)

      print(res)

      for x in as_completed(res):
        print(x)
    
    return res

# /pool

# --- classes

# this needs to be redone
# # Console is a rich console wrapper for beautifying statuses
# class Console:
#   T = SimpleNamespace(
#     clk="deep_sky_blue1", # timer
#     st="bold dark_cyan", # status + print
#     fail="bold red", # fail
#     inp="bold yellow", # in-progress
#     nbx="bold bright_black", # text with NBX at top and bottom
#     rule="dark_cyan", # ruler at top and bottom
#     spinner="weather", # status theme
#   )
# 
#   def __init__(self):
#     self.c = richConsole()
#     self._in_status = False
#     self.__reset()
# 
#   def rule(self, title: str):
#     self.c.rule(f"[{self.T.nbx}]{title}[/{self.T.nbx}]", style=self.T.rule)
# 
#   def __reset(self):
#     self.st = time()
# 
#   def __call__(self, x, *y):
#     cont = " ".join([str(x)] + [str(_y) for _y in y])
#     if not self._in_status:
#       self._log(cont)
#     else:
#       self._update(cont)
# 
#   def sleep(self, t: int):
#     for i in range(t):
#       self(f"Sleeping for {t-i}s ...")
#       _sleep(1)
# 
#   def _log(self, x, *y):
#     cont = " ".join([str(x)] + [str(_y) for _y in y])
#     t = str(timedelta(seconds=int(time() - self.st)))[2:]
#     self.c.print(f"[[{self.T.clk}]{t}[/{self.T.clk}]] {cont}")
# 
#   def start(self, x="", *y):
#     self.__reset()
#     cont = " ".join([str(x)] + [str(_y) for _y in y])
#     self.status = self.c.status(f"[{self.T.st}]{cont}[/{self.T.st}]", spinner=self.T.spinner)
#     self.status.start()
#     self._in_status = True
# 
#   def _update(self, x, *y):
#     t = str(timedelta(seconds=int(time() - self.st)))[2:]
#     cont = " ".join([str(x)] + [str(_y) for _y in y])
#     self.status.update(f"[[{self.T.clk}]{t}[/{self.T.clk}]] [{self.T.st}]{cont}[/{self.T.st}]")
# 
#   def stop(self, x):
#     self.status.stop()
#     del self.status
#     self._log(x)
#     self._in_status = False
