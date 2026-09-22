# Reproduction Checklist

Use this checklist for any new full regeneration or release rebuild.

1. Create and activate a clean Python virtual environment.
2. Install `requirements.txt`. For the documented verified stack, use `requirements-generator-verified.txt`.
3. Record `python --version`.
4. From the repository root, run `python scripts/capture_environment.py > environment_summary.txt`.
5. Run `python -m pip freeze > environment_lock.txt`.
6. Run `python src/generate_v4_0.py`.
7. Confirm `src/dhaka_smart_waste_v4_0_2025.h5` is created.
8. Run `python scripts/validate_v4_0.py`.
9. Confirm structural values: 5,000 bins, 365 days, 8,760 hours/bin, 43,800,000 rows.
10. Export/reconstruct `bins.parquet` plus 92 observation Parquet parts.
11. Place the reconstructed release under `final_parts/PARQUET/`.
12. Run `python scripts/validate_export_parts.py final_parts`.
13. Confirm 92 observation parts; parts 000–090 = 480,000 rows each; part 091 = 120,000 rows; total = 43,800,000 rows.
14. For the distributed 23-ZIP Drive release, install `requirements-validation.txt` and run `scripts/validate_v4_0_paper.py` with `--project-root` pointing to the release root.
15. Preserve environment summaries, validation reports, release manifests, and SHA-256 hashes with the release record.

The dataset is synthetic. Reproduction and validation establish deterministic/release consistency, not empirical field validation of deployed municipal smart bins.
