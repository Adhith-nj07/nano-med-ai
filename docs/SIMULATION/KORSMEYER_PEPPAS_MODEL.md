# Korsmeyer-Peppas Model

## Equation
`	ext
M_t / M_inf = k * t^n
`
Where k is the release constant and 
 is the release exponent indicating the mechanism of transport.

## Implementation Details
The model evaluates fractional release over time. To preserve mathematical validity:
1. Fractional release is hard-capped at 1.0 (100%).
2. Exceeding max_valid_fraction (default 60%) flags the state uncertainty as extrapolation rather than within_model_domain.

## Mechanism Limitations
The value of 
 is often used to interpret Fickian vs. non-Fickian diffusion. However, for spherical particles ( \approx 0.43$ for Fickian), fitting errors and small sample constraints mean 
 is treated empirically rather than definitively assigning physical morphology.
