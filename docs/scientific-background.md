# Scientific Background: Biological Clocks & Multi-Omics Aging

## 1. The Epigenetic Clock Paradigm

Chronological age records elapsed solar time since birth. In contrast, **biological age** reflects the cumulative physiological and molecular wear accrued across tissues, organ systems, and genomes.

In 2013, Steve Horvath published the multi-tissue DNA methylation clock based on 353 CpG dinucleotides, demonstrating that cytosine methylation state correlates tightly with chronological age across human tissues ($r \approx 0.96$). Hannum et al. simultaneously introduced a blood-based clock utilizing 71 CpGs. Subsequent generations of biological clocks (PhenoAge, GrimAge, DunedinPACE) integrated phenotypic mortality biomarkers and pace-of-aging trajectories.

### Molecular Hallmarks in BioAge-X

1. **Epigenetic Alterations**: Age-associated promoter hypermethylation at Polycomb repressive complex target loci (e.g. *ELOVL2*, *FHL2*) contrasted with global genomic hypomethylation.
2. **Cellular Senescence & SASP**: Stable cell cycle arrest mediated by *CDKN2A* ($p16^{\text{INK4a}}$) and *CDKN1A* ($p21^{\text{CIP1}}$), coupled with secretion of pro-inflammatory cytokines (*IL6*, *CXCL8*, *TNF*) known as the Senescence-Associated Secretory Phenotype.
3. **Deregulated Nutrient Sensing**: Hyperactive mTOR signaling accelerating anabolic stress, contrasted with downregulation of longevity factors (*SIRT1*, *FOXO3*, *KLOTHO*).
4. **Telomere Attrition**: Progressive erosion of telomeric repeats (*TERT*, *POT1*) precipitating critical DNA damage checkpoints.
5. **Mitochondrial Dysfunction & ROS**: Accumulation of oxidative stress and mitophagic decline (*SOD2*, *PINK1*).

## 2. Explainability and Biological Network Topology

Rather than operating as a black-box regression engine, BioAge-X maps predictive features back into known biological interaction topologies. SHAP attributions reveal which specific loci accelerate or decelerate age estimates in each patient, and Graph Neural Networks model message-passing between functional interactome neighbors.
