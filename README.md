# cnoidal -- Rust library for reading/writing EDA waveform files

> In fluid dynamics, a cnoidal wave is a nonlinear and exact periodic wave solution of the Korteweg–de Vries equation.

aka "I was trying to come up with a pun involving conflating electrical waves and water waves, but all of the easy ones have already been taken"

**VERY VERY WIP**

This library aims to handle reading/writing FST/LXT/LXT2/VZT/GHW? files without any C code.

## Design goals/ideas

* no C code
* `no_std`?
    * requires `alloc` when reading
    * no or optional `alloc` for writing
* simultaneous read/write not supported
* does not write temporary files (tradeoff for memory usage instead)
* O(n_vars) max memory usage -- metadata information can be kept in memory but value changes (past a certain point) will be flushed to disk. no reading the entire file into memory

## References/notes

* [FST format](https://blog.timhutt.co.uk/fst_spec/)
* [other GTKWave formats](format_notes.md)
