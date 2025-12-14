TFM Profiling Output
==================================================

This directory contains profiling data from TFM.

Analyzing Profile Files:
--------------------------------------------------

Using pstats (built-in):
  python -m pstats <profile_file>.prof
  Then use commands like:
    sort cumulative
    stats 20
    callers function_name

Using snakeviz (visual):
  pip install snakeviz
  snakeviz <profile_file>.prof

Profile File Naming:
--------------------------------------------------
  key_profile_YYYYMMDD_HHMMSS_microseconds.prof
  render_profile_YYYYMMDD_HHMMSS_microseconds.prof

