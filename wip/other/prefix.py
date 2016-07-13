

def lc_prefix(prefix, s):
  """return the longest common prefix of prefix and s"""
  if prefix is None:
    return s
  n = 0
  for i, j in zip(prefix, s):
    if i != j:
      break
    n += 1
  return prefix[:n]

def lc_suffix(suffix, s):
  """return the longest common suffix of suffix and s"""
  if suffix is None:
    return s
  return lc_prefix(suffix[::-1], s[::-1])[::-1]
