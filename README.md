# Critical Model Lifecycle Dependency for Scientific Progress

**Wenchao Dong**<sup>1</sup>, **Marcelo Sartori Locatelli**<sup>2</sup>, **Virgilio Almeida**<sup>3</sup>, **Meeyoung Cha**<sup>1,4</sup>

<sup>1</sup>MPI-SP, Germany · <sup>2</sup>Cornell University, USA · <sup>3</sup>UFMG, Brazil · <sup>4</sup>KAIST, South Korea

*EACL 2027 main conference paper.*

## Contents

```
data/
  extraction/     per-paper model and affiliation annotations (Gemma-4-31B-it)
  external/       World Bank GDP per capita
  aggregated/     derived tables written by the scripts (flags, credit weights,
                  Gini series, venue/country rates, country-year usage with GDP)
code/             six scripts that reproduce the reported results
results/          the reproduced figures (PDF) and tables (text)
```

`data/README.md` documents every file and column.

## Licences

- **Code** (`code/`): MIT, see `LICENSE`.
- **Our annotations and derived data** (`data/extraction`, `data/aggregated`,
  `results/`): CC BY 4.0.
- **Original paper content**: venues use different licences. For instance, the ACL
  Anthology uses CC BY-NC-SA 3.0 for papers published before 2016 and CC BY 4.0 from 2016
  onwards, while *Computational Linguistics* uses CC BY-NC-ND. We therefore do
  not redistribute the original content of the papers.
- **World Bank data** (`data/external`): World Development Indicators, release
  of 2026-07-13, CC BY 4.0, © The World Bank.

## Citation

```bibtex
@inproceedings{dong2027critical,
  title     = {Critical Model Lifecycle Dependency for Scientific Progress},
  author    = {Dong, Wenchao and Locatelli, Marcelo Sartori and Almeida, Virgilio and Cha, Meeyoung},
  booktitle = {Proceedings of the Conference of the European Chapter of the Association for Computational Linguistics (EACL)},
  year      = {2027},
  publisher = {Association for Computational Linguistics}
}
```
