# Report

**[Proxy-Tail-Anatomy-of-a-Failed-Research-Line-on-LLM-Evaluation-in-Finance.pdf](Proxy-Tail-Anatomy-of-a-Failed-Research-Line-on-LLM-Evaluation-in-Finance.pdf)** — *Proxy Tail: Anatomy of a Failed Research Line on LLM Evaluation in
Finance*, by Letao (Theodore) Ouyang. Ten pages in the ACL format: the research route with the
reasoning at each fork, a root-cause analysis, the results that survive, the practical significance
of the failure, a hindsight audit of what each stage cost and what would have closed it sooner, and
five questions for the next project.

## Building

The source is in [`src/`](src/): `main.tex`, `references.bib`, and the official ACL style files
`acl.sty` and `acl_natbib.bst` (from
[acl-org/acl-style-files](https://github.com/acl-org/acl-style-files), commit `d5adc82`). The
figures are drawn with TikZ inside `main.tex`. [`figures/`](figures/) holds PNG crops of Figures 1
and 2 from the built PDF.

With [Tectonic](https://tectonic-typesetting.github.io/):

```sh
cd report/src
tectonic main.tex
```

With a TeX Live or MiKTeX installation:

```sh
cd report/src
pdflatex main && bibtex main && pdflatex main && pdflatex main
```

The PDF in this folder was built with Tectonic 0.17.0.
