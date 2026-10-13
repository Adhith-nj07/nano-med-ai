# Drug Release Provenance Rules

Every imported experimental row must carry strict provenance to ensure scientific integrity:

1. **source_id**: Unique identifier linking to the raw CSV/Excel.
2. **DOI**: Digital Object Identifier of the source publication.
3. **normalization_applied**: Document any conversions (e.g., Days to Hours, Fractional release to Percentage).

*No synthetic interpolations (e.g., "guessing" t=12h because t=8h and t=24h exist) are allowed in the gold-standard dataset.*
