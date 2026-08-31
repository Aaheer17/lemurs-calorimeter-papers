<!-- GENERATED FILE — edit papers.yaml, then run scripts/build.py -->

# LEMURS Calorimeter Papers

Papers that use or relate to the [LEMURS](https://arxiv.org/abs/2509.05108) multi-detector electromagnetic calorimeter shower dataset.

Tracked monthly. The organising question is narrower than "fast calorimeter simulation": **does this work actually train on LEMURS?** Citing the dataset in related work is not the same thing, and the tiers keep that distinction visible.

## Tiers

| Tier | Meaning |
|------|---------|
| **0** | The dataset |
| **1** | Trains on LEMURS |
| **2** | Transfer and adaptation, not on LEMURS |
| **3** | Direct antecedents of Tier 1-2 work |

## Index

| Paper | Tier | LEMURS | Repr. | Code |
|-------|------|--------|-------|------|
| [LEMURS dataset: Large-scale multi-detector ElectroMagneti…](https://arxiv.org/abs/2509.05108) | 0 | yes | fixed-grid | yes |
| [A Generalisable Generative Model for Multi-Detector Calor…](https://arxiv.org/abs/2509.07700) | 1 | yes | fixed-grid | yes |
| [A universal vision transformer for fast calorimeter simul…](https://arxiv.org/abs/2601.05289) | 1 | yes | fixed-grid | ? |
| [Transferable Fast Calorimeter Shower Generation via Multi…](https://arxiv.org/abs/2608.18233) | 1 | yes | point-cloud | ? |
| [Cross-geometry transfer learning in fast electromagnetic…](https://arxiv.org/abs/2512.00187) | 2 | no | point-cloud | ? |
| [Transfer Learning Across Fast- and Full-Simulation Domain…](https://arxiv.org/abs/2605.07471) | 2 | no | n/a | ? |
| [AllShowers: One model for all calorimeter showers](https://arxiv.org/abs/2601.11716) | 3 | no | point-cloud | yes |
| [CaloArt: Large-Patch x-Prediction Diffusion Transformers…](https://arxiv.org/abs/2605.12011) | 3 | no | fixed-grid | ? |
| [CaloTrilogy: Toward a Breakthrough in One-Step, End-to-En…](https://arxiv.org/abs/2606.04165) | 3 | no | fixed-grid | ? |
| [CaloHadronic: a diffusion model for the generation of had…](https://arxiv.org/abs/2506.21720) | 3 | no | point-cloud | ? |
| [Generalizable foundation models for calorimetry via mixtu…](https://arxiv.org/abs/2603.28804) | 2 | no | voxel tokens (30x30x30, next-token) | yes |
| [SPADE: Split-and-Delay Embeddings for Autoregressive High…](https://arxiv.org/abs/2606.11304) | 3 | no | point-cloud | ? |

## Tier 0 — The dataset

*The anchor. Everything else is positioned relative to this.*

### LEMURS dataset: Large-scale multi-detector ElectroMagnetic Universal Representation of Showers

**McKeown, Peter, Raikwar, Piyush, Zaborowska, Anna** · n.d.

[arXiv:2509.05108](https://arxiv.org/abs/2509.05108) · [PDF](https://arxiv.org/pdf/2509.05108) · [INSPIRE](https://inspirehep.net/literature/2966931)

**Uses LEMURS:** yes · **Representation:** fixed-grid · **Code:** available · **Geometries:** Par04SiW, Par04SciPb, ODD, FCCeeCLD, FCCeeALLEGRO

Anchor dataset. 5M photon-induced EM showers evenly split across five detectors, on a cylindrical Universal Grid Representation independent of readout structure. More statistics, wider incident angles and multiple geometries relative to CaloChallenge dataset 2. HDF5. Used to build CaloDiT-2, which ships in Geant4 11.4.beta.

## Tier 1 — Trains on LEMURS

*Pre-trains or fine-tunes on the dataset itself.*

### A Generalisable Generative Model for Multi-Detector Calorimeter Simulation

**Raikwar, Piyush, Zaborowska, Anna, McKeown, Peter, Cardoso, Renato, *et al.* (6 authors)** · n.d.

[arXiv:2509.07700](https://arxiv.org/abs/2509.07700) · [PDF](https://arxiv.org/pdf/2509.07700) · [INSPIRE](https://inspirehep.net/literature/2968066)

**Uses LEMURS:** yes · **Pre-train:** LEMURS (4 geometries) · **Target:** new detectors; CaloChallenge ds2 benchmark · **Representation:** fixed-grid · **Code:** available

Diffusion model with transformer blocks. Pre-trains across multiple detectors and adapts to new ones, reporting up to 25x less data and 20x less training time. 900k train / 100k validation showers per detector. Stated as the first published pre-trained model supporting adaptation for shower simulation. Overlapping author list with the LEMURS dataset.

### A universal vision transformer for fast calorimeter simulations

**Favaro, Luigi, Giammanco, Andrea, Krause, Claudius** · n.d.
  
*Mach. Learn.: Sci. Technol. 7(3) 035052 (2026)*

[arXiv:2601.05289](https://arxiv.org/abs/2601.05289) · [PDF](https://arxiv.org/pdf/2601.05289) · [INSPIRE](https://inspirehep.net/literature/3100141)

**Uses LEMURS:** yes · **Pre-train:** LEMURS · **Target:** CaloChallenge ds2, ds3, CaloHadronic · **Representation:** fixed-grid · **Code:** unverified

ViT surrogate pre-trained on LEMURS. At 100k training showers the fine-tuned model beats from-scratch training on CaloChallenge ds2. Gains on high-granularity ds3 are smaller, plateauing near AUC 0.80, which the authors suggest may reflect network expressivity rather than the transfer method.

### Transferable Fast Calorimeter Shower Generation via Multi-Geometry Pre-training

**Buss, Thorsten, Day-Hall, Henry, Gaede, Frank, Kasieczka, Gregor, *et al.* (7 authors)** · n.d.

[arXiv:2608.18233](https://arxiv.org/abs/2608.18233) · [PDF](https://arxiv.org/pdf/2608.18233) · [INSPIRE](https://inspirehep.net/literature/3192605)

**Uses LEMURS:** yes · **Pre-train:** SimpleBox (10^4 synthetic box calorimeters) vs LEMURS · **Target:** FCCee-ALLEGRO (held out) · **Representation:** point-cloud · **Code:** unverified

Compares a synthetic pre-training pool against a realistic one. With 10^3 target showers, the two priors reduce aggregated sliced Wasserstein distance to Geant4 by 5.2x (synthetic) and 8.0x (realistic) versus from-scratch. Reports that as fine-tuning data grows, the LEMURS-pretrained model moves away from the Geant4 ALLEGRO reference and toward its own pre-training value; the SimpleBox arm moves toward its own pool; the from-scratch arm shows no trend. Builds on the AllShowers backbone. NOTE: sometimes miscited as "CaloART" — it is not CaloArt (see caloart).

## Tier 2 — Transfer and adaptation, not on LEMURS

*Same family of question, different data. Note the transfer axis on each entry: geometry, material+species and fidelity results are not directly comparable to one another.*

### Cross-geometry transfer learning in fast electromagnetic shower simulation

**Gaede, Frank, Kasieczka, Gregor, Valente, Lorenzo** · n.d.

[arXiv:2512.00187](https://arxiv.org/abs/2512.00187) · [PDF](https://arxiv.org/pdf/2512.00187) · [INSPIRE](https://inspirehep.net/literature/3088057)

**Uses LEMURS:** no · **Transfer axis:** geometry · **Pre-train:** International Large Detector (ILD) · **Target:** CaloChallenge ds3 · **Representation:** point-cloud · **Code:** unverified

Point-cloud transfer learning without re-voxelisation. With 100 target-domain samples, reports a 44% improvement on the geometric mean of Wasserstein distance over from-scratch training. Bias-only PEFT stays competitive while updating 17% of parameters. Cites LEMURS only in related work, contrasting itself with CaloDiT-2 on single- vs multi-detector pre-training and point-cloud vs fixed-grid representation. Named in multigeom-pretrain as its closest precursor.

### Transfer Learning Across Fast- and Full-Simulation Domains in High-Energy Physics

**Schott, Matthias, Flek, Lucie** · n.d.

[arXiv:2605.07471](https://arxiv.org/abs/2605.07471) · [PDF](https://arxiv.org/pdf/2605.07471) · [INSPIRE](https://inspirehep.net/literature/3153548)

**Uses LEMURS:** no · **Transfer axis:** fidelity · **Pre-train:** ATLAS-like Delphes fast simulation · **Target:** CMS-like Delphes fast sim; fully simulated ATLAS Open Data · **Representation:** n/a · **Code:** unverified

Transfer between fast-simulated and fully simulated datasets across three tasks: signal-background classification, quark-gluon tagging, and missing transverse energy reconstruction, using dense, graph and transformer architectures. Pre-trained models beat independently trained baselines throughout and cut required target-domain statistics by roughly a factor of two. Not shower generation and not cross-geometry — the transfer axis is simulation fidelity, so its numbers are not on the same footing as the geometry-axis results elsewhere in this tier.

### Generalizable foundation models for calorimetry via mixtures-of-experts and parameter efficient fine tuning

**Cardona-Giraldo, Carlos, Fanelli, Cristiano, Giroux, James, Granger, Cole, *et al.* (6 authors)** · n.d.

[arXiv:2603.28804](https://arxiv.org/abs/2603.28804) · [PDF](https://arxiv.org/pdf/2603.28804) · [INSPIRE](https://inspirehep.net/literature/3137580) · [code: github.com](https://github.com/wmdataphys/FM4CAL) · [data: github.com](https://github.com/FLC-QU-hep/getting_high)

**Uses LEMURS:** no · **Transfer axis:** material+species · **Pre-train:** ILD Si-W ECAL, photons in tungsten + tantalum (~950k samples each) · **Target:** photons in lead; electrons in W/Ta/Pb · **Representation:** voxel tokens (30x30x30, next-token) · **Code:** available

Next-token transformer foundation model. Fixed-routing Mixture-of-Experts handles materials; new materials are added by training one expert with the backbone frozen, reaching agreement within uncertainty at 1k fine-tuning samples. New particle species need LoRA (r=128) plus particle-specific vocabulary heads, working well from 50k samples. Because adaptation is strictly additive on a frozen backbone, catastrophic forgetting is prevented by construction. Reports 392x speedup over Geant4 using KV-cache, memory preallocation and CUDA graphs. Datasets are ILD-based, replicating Getting High and OmniJet-alpha_c; the transfer axis is material and particle species, not detector geometry.

## Tier 3 — Direct antecedents of Tier 1-2 work

*A Tier 1-2 paper builds on these or benchmarks against them.*

### AllShowers: One model for all calorimeter showers

**Buss, Thorsten, Day-Hall, Henry, Gaede, Frank, Kasieczka, Gregor, *et al.* (5 authors)** · n.d.

[arXiv:2601.11716](https://arxiv.org/abs/2601.11716) · [PDF](https://arxiv.org/pdf/2601.11716) · [INSPIRE](https://inspirehep.net/literature/3109187) · [code: github.com](https://github.com/FLC-QU-hep/AllShowers)

**Uses LEMURS:** no · **Pre-train:** ILD · **Representation:** point-cloud · **Code:** available

Single generative model covering multiple particle types, replacing per-species networks. Continuous normalizing flow with a Transformer over variable-length point clouds. Reported to exceed prior single-particle-type models on hadronic fidelity. This is the backbone multigeom-pretrain builds on — read first.

### CaloArt: Large-Patch x-Prediction Diffusion Transformers for High-Granularity Calorimeter Shower Generation

**Huang, Zhengkun, Sun, Gongxing** · n.d.

[arXiv:2605.12011](https://arxiv.org/abs/2605.12011) · [PDF](https://arxiv.org/pdf/2605.12011) · [INSPIRE](https://inspirehep.net/literature/3154649)

**Uses LEMURS:** no · **Target:** CaloChallenge ds2, ds3 · **Representation:** fixed-grid · **Code:** unverified

DiT-style backbone for direct raw voxel generation, with 3D axial RoPE, RMSNorm, qk-norm and shared conditioning modulation, trained via conditional flow matching with decoupled prediction and loss spaces. On ds2 reports best FPD and strongest high-level and ResNet classifier metrics; on the 40500-voxel ds3, x-prediction beats v-prediction on all reported metrics. This is the real CaloArt — single-geometry, not multi-geometry pre-training.

### CaloTrilogy: Toward a Breakthrough in One-Step, End-to-End, Physics-Guided Shower Generation for Modern Calorimeters

**Jiang, Cheng, Qian, Sitian, Pedro, Kevin, Amram, Oz, *et al.* (6 authors)** · n.d.

[arXiv:2606.04165](https://arxiv.org/abs/2606.04165) · [PDF](https://arxiv.org/pdf/2606.04165) · [INSPIRE](https://inspirehep.net/literature/3165001)

**Uses LEMURS:** no · **Representation:** fixed-grid · **Code:** unverified

One- or few-step generation combining a MeanFlow average-velocity integrator, a conditional-GMM prior learned in shower space rather than from noise, and physics-guided loss terms. Addresses the O(100) function evaluations typical of flow-matching and diffusion surrogates. Cites the full cluster above, so it doubles as a current map of the field.

### CaloHadronic: a diffusion model for the generation of hadronic showers

**Buss, Thorsten, Gaede, Frank, Kasieczka, Gregor, Korol, Anatolii, *et al.* (7 authors)** · n.d.
  
*JINST 21(01) P01042 (2026)*

[arXiv:2506.21720](https://arxiv.org/abs/2506.21720) · [PDF](https://arxiv.org/pdf/2506.21720) · [INSPIRE](https://inspirehep.net/literature/2939411)

**Uses LEMURS:** no · **Pre-train:** ILD · **Representation:** point-cloud · **Code:** unverified

Transformer extension of geometry-independent point-cloud diffusion to hadronic showers, generating across both electromagnetic and hadronic calorimeters. Used as a fine-tuning target in universal-vit.

### SPADE: Split-and-Delay Embeddings for Autoregressive High-Granularity Calorimeter Simulation

**Birk, Joschka, Gaede, Frank, Hallin, Anna, Kasieczka, Gregor, *et al.* (6 authors)** · n.d.

[arXiv:2606.11304](https://arxiv.org/abs/2606.11304) · [PDF](https://arxiv.org/pdf/2606.11304) · [INSPIRE](https://inspirehep.net/literature/3167516)

**Uses LEMURS:** no · **Target:** Getting High and Getting Square photon datasets (ILD) · **Representation:** point-cloud · **Code:** unverified

Autoregressive high-granularity shower simulation with split-and-delay embeddings. Trains AllShowers as a baseline on the same photon datasets, and gives an independent description of that architecture: PointCountFM predicts points per layer and fixes each point's z from the layer index, then a CNF-transformer predicts (x, y, E), reducing the generative task to three dimensions.

## Background

Widely cited work with no traceable link to LEMURS. Listed so it is findable and citable, but deliberately untiered — everything above would be pointless if LEMURS did not exist, and these would not.

- [CaloChallenge 2022: a community challenge for fast calorimeter simulation](https://arxiv.org/abs/2410.21611) — Krause et al., n.d.. Community benchmark most papers here report against.
- [Lantern: Conflict-Aware Gradient Blending for Physics-Guided Diffusion Models in Calorimeter Simulation](https://arxiv.org/abs/2607.25060) — Farzana Yasmin Ahmad et al., 2026. Introduces CFD, a correlation-structure metric alongside FPD/KPD.

---

## How this is maintained

`papers.yaml` is the only file edited by hand. `README.md` and `papers.bib` are generated from it by `scripts/build.py`, which pulls titles, authors, dates and BibTeX from INSPIRE — falling back to the arXiv API for papers with no INSPIRE record.

Suggestions welcome: open an issue with the arXiv ID. Papers that use LEMURS but aren't listed are especially useful, since the citation watchers under-cover work filed outside the physics categories.

## License

Code in `scripts/` is MIT — see [LICENSE](LICENSE).  
The paper list and annotations are CC BY 4.0 — see [LICENSE-CONTENT](LICENSE-CONTENT).

Bibliographic metadata (titles, authors, identifiers) are facts and are not claimed under either license. Summaries are paraphrases written for this repo, not publisher abstracts.
