# Production Machinery v12

Implemented:
- sound future-core degree upper-bound pruning;
- durable UoW state for each m=33..54 bucket;
- production canonical/coloring backend interfaces;
- SAT acceptance requires explicit coloring; UNSAT acceptance requires a proof artifact;
- named authority dependency gate for EFL/EFL' equivalence, SAT-2023 outside-bucket coverage, and the degree-13-core reduction;
- final n=13 closure gate requiring all 22 bucket artifacts plus all authority dependencies.

Still external/scale dependencies rather than missing semantics:
1. scalable canonical-labeling implementation behind CanonicalBackend;
2. proof-producing SAT/SMS coloring/generation implementation behind ColoringBackend;
3. verified ingestion of the three named external authority artifacts;
4. actual execution of the 22 bucket campaigns;
5. for the full uniform EFL problem beyond n=13, an effective cutoff or new uniform theorem.
