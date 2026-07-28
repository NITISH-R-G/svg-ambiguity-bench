# Glossary

Fixed meanings. Used consistently in code, docs, and the report.

| Term | Meaning |
|---|---|
| **ambiguity set** | The K elements in an SVG sharing an identical tag and fill, with redacted geometry. The candidates an instruction must disambiguate between. |
| **K** | Size of the ambiguity set, 4–7. Sets the random-selection floor at `1/K`. |
| **distractor** | An element outside the ambiguity set (different tag or fill). Present so the scene is not uniformly one kind of thing. |
| **case** | The atomic experimental unit: one SVG + one instruction. Identical across all arms. |
| **arm** | An experimental condition. Arms differ only in the injected context block. |
| **cell** | A reporting group, e.g. arm × predicate or arm × family. |
| **cluster** | An SVG. The unit of statistical resampling, because instructions sharing an SVG are not independent. |
| **replicate** | A repeated model call on the same case. Never enters `n`. |
| **predicate** | A formally defined visual property, e.g. `top_left`, `second_largest`. Registry entries with an operational definition and a margin. |
| **family** | A group of predicates: `SPATIAL` or `ORDINAL_SIZE`. |
| **operation** | The edit to perform: recolor fill, add stroke, delete, rotate. |
| **margin** | How decisively the intended target beats the runner-up on its predicate. Low margin = contested = rejected at generation. |
| **geometry token** | The fixed-length opaque string replacing a `d` attribute. Also the primary scoring identity anchor. |
| **resolved SVG** | Real path data. Used for rendering and ground truth. Never shown to a model. |
| **model-visible SVG** | Redacted. Exactly what the model sees. |
| **ground truth** | Machine-derived per-element geometry and predicate winners. Never shipped to a model in any arm. |
| **context block** | Text injected into the prompt's one slot. Empty for `baseline`. The only difference between arms. |
| **identification** | The model acted on the intended element. **The primary metric.** |
| **execution** | The edit matched the operation spec. |
| **collateral** | Elements other than the target were modified. The hedging signal. |
| **strict** | identification ∧ execution ∧ no collateral. Secondary. |
| **loose** | identification ∧ execution. Trivially gamed by editing everything; never reported alone. |
| **abstention** | The model explicitly declined, citing insufficient information. A distinct outcome, not a failure. |
| **dataset hash** | Content-addressed root hash of the frozen corpus. Arms load by it and refuse on mismatch. |
| **pre-registration boundary** | The git tag after which scoring and metrics may only change by disclosed amendment. |
| **manipulation check** | An experimental condition whose job is to verify the manipulation worked — here, `baseline`. Not the benchmark. |
