# Local foundations experiment: pre-run budget and constraints

## Questions to test
Determinism, accounting identities and exact contamination for WP0.5; the four-configuration, three-seed comparison for WP0.2. The exact integer computation and exhaustive proof checks for T1.4 are also run; they are theoretical numeric checks, not main-line training after passing G0.

## Budget (recorded before the run)
- CPU, 0 GPU memory; about 600 synthetic training/evaluation families, 3 training seeds.
- Expected: data generation and integer checks < 1 minute; small text encoder, four configurations × three seeds, < 10 minutes in total, memory < 2 GB. This is a budget, not a measurement.
- No external data, models or weights are downloaded. Only new local code is run.
- The text model is trained from random initialization with mean embedding + MLP and is not claimed to be a pretrained language model; the results only test the foundation pipeline and the synthetic permission specifications.
- These results are not used to pass G0/G1 on real data, and Phase 1 shard-model training is not run.

## Configuration
- Base commit: 8e4dd0b33c95ac2ac1a6015eba6f2dfafe5c1254; new source files are pinned by a SHA256 manifest.
- Data seed 20261115; training seeds 11, 23, 47; chronological family split.
- Measured time, environment, data hashes and metrics are written by the script as JSON.

## Results and limits
After the run, see `results.json` and `report.md` in the same directory. No results are filled in before execution.
