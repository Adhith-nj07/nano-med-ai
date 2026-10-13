# Physical Stability Digitization Protocol

## Digitization Standard
When harvesting must rely on figure digitization:
1. **Extraction**: Use a tool (e.g., WebPlotDigitizer) to map axes.
2. **Metadata**: Log `figure_coordinate_system`, `axis_scale`, and `axis_units`.
3. **Tagging**: All resulting points MUST be tagged `digitized_from_figure`.
4. **Verification**: A verification artifact (plot of extracted points over original axes) must be retained internally.

## Cautions
- Do not assume bar chart error bars represent standard deviation without verifying the legend.
- Do not interpolate between digitized points.
