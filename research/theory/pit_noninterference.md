# Point-in-time log projection, historical non-interference, and identifiability limits

Date: 2026-11-16. Status: PNI1–PNI6 below are complete conditional propositions with pen-and-paper proofs; they are not formally verified in Lean. Only the object definitions from the local [T1.1](notes.md) and from work package WP1.2 are used; no internet access, no training, no changes to the implementation. This file corrects "tests as constructive certificates" to: **the construction gives a conditional general argument, tests check the finite behaviour of the actual implementation, and neither can substitute for the other**. These factorizations, compositions of measurable functions, and necessary conditions for identification are general facts, and no theoretical novelty is claimed on their basis.

The PIT reference pipeline is a theorem interface and implementation evidence, not new main-line model training, and it does not make G0 or G1 pass automatically. The historical authenticity of the source data still needs separate evidence. The sections below distinguish in particular between the visibility a record claims and true historical availability.

## 1. Object: a finite version log, not a final document table

Fix a cutoff time $`t`$. The event header of each event in a finite event log $`L=(e_1,\ldots,e_n)`$ contains:

- `event_id`: the immutable identity of the version event;
- `document_id`: the logical document identity;
- `knowledge_time`, written $`\kappa(e)`$: the declared time at which **all facts of this event that will be used** enter the allowed information set.

The event body contains the `operation`, the claimed `record_time`, and the full version payload. The payload may contain text, a content digest, the source, the core role, labels, and metadata; deletion is a tombstone event. The event time, the accounting period in the text, the source publication date, the original record time, and the knowledge time are different objects. The implementation should project by **knowledge_time**; a future revision may keep a very early `record_time`, but that must not be allowed to rewrite historical state retroactively.

Define the history projection

```math
H_t(L)=\mathrm{canon}\{e\in L:\kappa(e)\le t\}, \qquad (1.1)
```

where canon sorts by fixed historically visible keys (for example knowledge_time, event_id) and applies a deterministic encoding; it does not use the final log length, physical row numbers, future counts, or final global version numbers as tie-breaks. $`H_t`$ contains all visible version events, and **does not first take only the latest version over the whole log**. The latest valid state is computed by a separate visible-event replayer $`R`$, $`X_t=R(H_t(L))`$.

To close the measure-theoretic part concretely, the theoretical input is taken to be a valid subset of finite byte/JSON encodings with integer times, with the discrete $`\sigma`$-algebra. Finite byte strings of finite length form a countable space; the snapshot space $`ℋ_t=H_t(𝒟_t)`$ is also countable. If this is extended to arbitrary uncountable data objects, a measurable section, a suitable quotient space, or an explicit measurable construction must be supplied separately; a measurable factor cannot be inferred directly from a set-theoretic factorization.

**An identical hash is not the definition.** Historical equivalence means that the canonical content of the projections is the same; a hash is only implementation evidence. Identical content necessarily produces the same deterministic hash, but the converse cannot be treated as a mathematical identity without a collision-freeness assumption. If a constructive proof needs input identity, it should keep a canonical content / object identity contract, rather than merely saying "the hashes are equal".

### 1.1 Field availability contract

The knowledge time of a full version upsert should be no earlier than the true allowed availability time of every field used in that version; formally, if the set of fields is $`F(e)`$, we need

```math
\kappa(e)\ge \max_{f\in F(e)}\tau_f^*(e). \qquad (1.2)
```

Actual point-in-time measurability also requires that whether an event is included, and the mechanism forming each identity and time metadata field, be historically adapted; the inequality above alone does not rule out the future deciding which old documents are kept. If a label comes from future returns or later human review, its availability time cannot be moved earlier by borrowing the headline's publication time. The same applies to source identity, the core flag, deduplication rules, model selection rules, and available validation labels.

The full-version approach conservatively delays an entire new version, while the old version can still be used before then. If fields are to be updated separately by time, the fields must be versioned or an equivalent replayable structure must be used; "back-filled" label/source fields must not be read from the current final object. A content-hash reference also needs the corresponding immutable bytes to have been available within the allowed time; being able to find a text today from an old hash does not prove those bytes existed in the past.

### 1.2 Domain and rejection results

Projection requires at least parsing the outer event header. Hence "all future extensions" means extensions with headers valid by convention: dictionary structure, nonempty identities, parsable knowledge times, and so on satisfy the contract. Corrupted data whose time cannot be determined at the outer level is outside the guarantee domain of the theorem; it should be reported as invalid input, and no claim is made that appending arbitrary malicious bytes cannot affect service availability.

At a fixed $`t`$, future event bodies may be opaque; their labels, content hashes, or core flags must not be read to decide whether the historical output is valid. First project by valid headers, then validate the visible event bodies. When a visible event body is invalid, a deterministic `Reject` can be included in the output space, still determined by the same $`H_t`$. Future errors go only into the audit appendix and must not turn a stable result under the same history from success into failure. If an implementation chooses to accept only the smaller domain where the whole log is valid, this restriction should be stated explicitly, and error handling outside the domain must not also be claimed as proved non-interference.

## 2. PNI1: historical-equivalence non-interference if and only if the output factors through the history projection

Fix the code/control configuration $`c`$ and the seed value $`\omega`$. Let the deterministic stable output be $`F_{t,c,\omega}:𝒟_t\to 𝒴`$; $`𝒴`$ contains all artifacts and states promised to be stable, not only the model weights. Define

```math
L\sim_t L'\quad\Longleftrightarrow\quad H_t(L)=H_t(L'). \qquad (2.1)
```

**Proposition PNI1.** The following are equivalent:

1. For any $`L,L'\in 𝒟_t`$, $`L\sim_t L'`$ implies $`F_{t,c,\omega}(L)=F_{t,c,\omega}(L')`$.
2. There exists a unique $`G_{t,c,\omega}:ℋ_t\to 𝒴`$ with $`F_{t,c,\omega}=G_{t,c,\omega}\circ H_t`$.

**Proof.** If 2 holds, the same history projection passed to the same function necessarily produces the same result, giving 1. If 1 holds, for any $`h\in ℋ_t`$ define $`G(h)`$ as $`F(L)`$ for any $`L`$ with $`H_t(L)=h`$. The definition of the image space guarantees such an $`L`$ exists; 1 guarantees that all such values are the same, so the definition is well defined and independent of the representative. Then $`G(H_t(L))=F(L)`$ for every $`L`$. If another function has the same factorization, taking each $`h=H_t(L)`$ in the image space in turn, its value must equal $`F(L)=G(h)`$, so it is unique. ∎

This is a purely set-theoretic proposition and needs no training algorithm, independence of randomness, accuracy, or real time evidence. In the countable discrete spaces of this section, the factor is measurable; if the output also depends on a random $`\Omega`$ and $`F(L,\cdot)`$ is measurable for each fixed log, one can fix a representative in each countable history fibre and assemble $`G(h,\omega)`$ into a measurable function. **On general measurable spaces, being constant on fibres does not by itself guarantee this measurability conclusion.**

An equivalent historical summary need not be exactly the final document state $`X_t`$. If the training policy depends on the number of historical revisions or on the source trajectory up to $`t`$, the version events in $`H_t`$ can still legitimately be used; if only $`X_t`$ is passed, one must separately prove that it is sufficient for the actual pipeline. Keeping $`H_t`$ by default avoids mistakenly collapsing different valid histories into one state.

## 3. PNI2: when pure future appends are equivalent to full historical non-interference

Write $`L\rightsquigarrow_t L'`$ for one valid pure future extension: every added event satisfies $`\kappa>t`$, no existing event identity, knowledge time, content, or exogenous configuration is changed, and $`H_t(L')=H_t(L)`$. Here we distinguish **logically adding events followed by canonical sorting** from **physically appending at the end of the file**.

**Proposition PNI2.** Historical non-interference always implies invariance under every valid pure future extension. Conversely, if for each $`h\in ℋ_t`$ there is a valid base log $`b_h`$ with $`H_t(b_h)=h`$, and every $`L`$ with projection $`h`$ can be reached from $`b_h`$ by finitely many valid pure future extensions, then "invariance under all valid one-step extensions" implies the historical non-interference of PNI1.

**Proof.** The forward direction uses directly that the projection is the same before and after an extension. For the converse, let the chain from $`b_h`$ to $`L`$ have length $`k`$; by induction on $`k`$, one-step invariance makes every output along the chain equal to $`F(b_h)`$. Hence any $`L,L'`$ with the same $`h`$ both equal $`F(b_h)`$, which gives non-interference. A chain of length zero corresponds to $`L=b_h`$, and the claim holds as well. ∎

**A commonly used sufficient condition.** Valid logs are sorted by knowledge time and a fixed tie-break; the historical prefix with $`\le t`$ is itself valid; every complete log is obtained from this prefix by successively appending valid events with $`>t`$, and all intermediate logs are valid. Then one can take $`b_h=h`$, and a general proof for one-step appends extends along the chain. The dependencies of update events must be resolvable at the time; an early record must not require a future parent version that has not yet appeared in order to be valid.

More generally, if each fibre of identical history is connected in the undirected graph of "valid future additions/deletions", invariance also propagates along paths. This shows that what is really needed is enough comparability, not a literal requirement that the file format be some prefix format.

**Counterexample when the reachability condition is missing.** Allow arbitrary physical order, and let the output be "the number of future records appearing before the last historical record", defined as 0 when there is no historical record. Appending any future event at the end of the file does not change this number, so the output is invariant under physical end-appends over the whole domain. Yet for $`L=[p]`$ and $`L'=[f,p]`$, with $`p`$ historical and $`f`$ future, both projections are $`[p]`$, while the outputs are 0 and 1 respectively. Although the history projection is valid, $`[f,p]`$ cannot be obtained from $`[p]`$ by end-appends alone. Hence **a valid projection alone is not enough**; the input should be canonicalized first, or the guarantee should be stated explicitly only for the domain of ordered logs.

**Counterexample for single-item tests.** If one tests only a single document addition from one base log with no future events, the program "flip the output only once the number of future documents reaches 2" passes every such single-item test, yet fails with two future appends. What fails here is the quantifier of the test; if invariance under every one-step append from every valid intermediate state has been proved, the induction of PNI2 rules out exactly this problem.

## 4. PNI3: project first, then replay versions, and the constructive pipeline

**Proposition PNI3.** Fix $`c,\omega,t`$. First take $`H_t(L)`$, validate and replay only its visible versions, and then run finitely many deterministic components in sequence:

```math
Z_0=(t,H_t(L),c,\omega),\qquad Z_k=f_k(Z_0,\ldots,Z_{k-1}),\quad k=1,\ldots,K. \qquad (4.1)
```

If no $`f_k`$ accesses any external state not expressed in its arguments, and the stable output is a deterministic serialization of these $`Z_k`$, then all components and the final stable output satisfy PNI1.

**Proof.** The same $`H_t`$ and $`c,\omega,t`$ give the same $`Z_0`$. Suppose the first $`k-1`$ states are the same; then the full input of $`f_k`$ is the same, and determinism gives the same $`Z_k`$. Induction over the finitely many components gives that all states are the same, and fixed serialization gives the same bytes. Each intermediate result is also explicitly a function of $`H_t`$, so it can be checked independently. ∎

**Special case of version replay.** For each document_id, among the visible events take the last full upsert/tombstone by $`(\kappa,event\_id)`$, or replay the equivalent state sequentially. The same projection gives the same visible event order and the same state. Future revisions, future tombstones, and future label/source/core changes are not in this input, so they do not affect old snapshots. A deletion is a new knowledge event and does not modify the bytes of old events; adding a record with an earlier knowledge time is back-filling history, not a pure future append, and is not covered by the append-invariance promise.

**Counterexample for taking the latest first and filtering afterwards.** The old version of a document has knowledge time 0 and text A; a revision has knowledge time 2 and text B, but keeps record_time=0. Take cutoff 1. Taking the latest over the whole table and then filtering by record_time includes B; taking the latest over the whole table and then filtering by knowledge_time drops A as well, which was originally available. The correct order is to filter $`\kappa\le1`$ first and then select A from the historical events.

The "determinism" of the algorithm includes sorting, tie rules, the order of PRNG consumption, and serialization. A fixed seed alone cannot guarantee bitwise determinism of multithreaded numerical libraries; reading the wall clock, environment variables, current network content, unpinned versions of files, or a shared cache also breaks the closed-input assumption. The reference pipeline can achieve determinism in a restricted runtime environment; if general training can only be shown to be identical in distribution, distributional non-interference should be reported, and it must not be passed off as pathwise bitwise invariance.

## 5. All shared components must come after the projection

The following are the concrete items that close the construction condition; this is not something achieved merely by adding a cutoff parameter to each function.

| Entry point | Valid construction | Explicit mechanism that violates the construction |
|---|---|---|
| Content, source, labels, core role | Use only visible full versions or field versions | Future labels back-filled in the current final table; future verification upgrading an old document to core |
| Filtering and document selection | Rules and the metadata they use are historically available; applied to $`H_t`$ | Future survival, final returns, or a posteriori high-quality sources deciding which old documents are kept |
| tokenizer / vocabulary / IDF | Fitted only on the historical training subset | Future text changing word frequencies, vocabulary capacity ranking, IDF, or unknown-word encoding |
| Deduplication | Build the graph on the historical set, take connected components, choose representatives by historical keys | A future bridging document joining two old clusters into one, changing sampling weights or representatives |
| Sampling | Start from historical candidates and historical sizes, sample with an exogenous seed | Using the full log length as denominator, consuming random numbers for future rows first, sampling the whole database first and then deleting the future |
| train/dev split | Stable IDs of historical candidates and a frozen rule | Rank in the final full-database order, or clusters formed in the future, changing the historical split |
| Validation and hyperparameters | Validation labels known by the decision time, candidates and selection rule fixed | Choosing C with future return labels, early stopping on future validation loss, choosing core by future performance |
| Missing values, standardization, and dictionaries | Only historical statistics and versioned lookups | Final financial restatements, the current entity dictionary, or full-sample means filling old missing values |
| Stable output identity | Deterministic encoding of the history projection, the historical configuration, and the versions used | Writing the final whole-log hash, future counts, or the current run time into the stable certificate |

**A concrete example of a deduplication bridge.** Add an edge when token-set Jaccard ≥$`4/5`$: the old sets $`A=\{1,2,3,4\}`$ and $`C=\{2,3,4,5\}`$ have similarity $`3/5`$ and originally belong to two clusters; the future $`B=\{1,2,3,4,5\}`$ has similarity $`4/5`$ with both, and building the graph on the full database merges the two old clusters. Even if B is deleted at the end, the old cluster structure has already been affected by the future. One should project first and then build the graph.

**The core role is not exempt.** `core=True` is an input that must have an availability time and a basis; it cannot bypass the history projection in the name of "the core is trusted". Confirming in the future that an old document is reliable cannot prove retroactively that the selection rule at the time already knew this. A single future-affected shared preprocessing step may change every shard, so it cannot be treated as merely one document of edge contamination either.

**The distinction for evaluation labels.** Predicting a future outcome and then evaluating with the future realized value is a normal part of defining a backtest statistic; that label must stay on the evaluation path after the prediction is generated. It must not flow back into the historical model's training, validation selection, or the stable predictor artifact. The prediction cutoff, the label availability time, and the final evaluation time must be recorded separately.

## 6. The stable certificate and the audit appendix must be kept separate

Let the full returned package be $`(Y_t,A_{\rm audit})`$. The non-interference promise applies only to the explicitly defined stable object

```math
Y_t=G(H_t(L),c,\omega), \qquad (6.1)
```

which may include the historical version state, the historically selected IDs, the vocabulary, grouping, sampling, split, hyperparameter decisions, and deterministic hashes of these artifacts. The audit appendix $`A_{\rm audit}`$ may record the raw input file hash, the final total row count, the number of ignored future events, the checker's run time, the environment, and diagnostics, but it must be marked as changing under future appends, and **must not feed back into any decision of $`Y_t`$**.

**Counterexample.** Even if the model weights are constant, if the stable certificate also contains `full_log_count`, appending one future event to the historical log increases this count by 1, and the whole certificate is no longer invariant. Likewise, the final whole-log hash usually changes. If the object of acceptance is the whole returned package, changes in the appendix cannot be described as "the certificate is still bitwise invariant"; one must make the verifiable projection $`\pi_{\rm stable}(Y_t,A_{\rm audit})=Y_t`$ explicit, or simply store the two separately.

The whole-file hash in the audit appendix serves provenance, but it is not a proof of measurability of the historical model. Switching to "only check that the weights are the same" is too weak as well, because the vocabulary, label order, core identities, or hyperparameter descriptions may have been changed by the future, and later inference behaviour and the interpretation of the certificate would differ.

## 7. PNI4: when record non-interference implies true point-in-time measurability

On the probability space of the real data world, let $`ℱ_t`$ denote the information **actually allowed** up to $`t`$. The record log is a random object $`L`$. The control configuration $`C_t`$ includes the choice of code/rules, candidate hyperparameters, external lookups, and the description of the random mechanism.

**Proposition PNI4.** If $`H_t(L)`$ and $`C_t`$ are $`ℱ_t`$-measurable and $`G`$ is measurable, then $`Y_t=G(H_t(L),C_t,\Omega)`$ is $`ℱ_t\vee\sigma(\Omega)`$-measurable. When the seed is fixed or the random source is included in $`ℱ_0`$ in advance, one obtains measurability with respect to the corresponding point-in-time information set.

**Proof.** $`H_t(L)`$, $`C_t`$, and $`\Omega`$ are all measurable with respect to the enlarged $`\sigma`$-algebra; the random vector they form is measurable, and composing with the measurable $`G`$ gives the result. If $`\Omega`$ already belongs to $`ℱ_t`$, the enlargement adds no information. ∎

This step **does not need independence**, and it does not automatically say that the seed after enlargement carries no future. The measurability proposition must be kept separate from the information restriction in the next section. Similarly, PNI1 does not require the seed to be random when comparing worlds with the seed fixed; but it cannot prevent an actual user from choosing the seed after seeing future results.

The substantive external premise of PNI4 is the true historical adaptedness of $`H_t(L)`$ and of the control choices. A field named knowledge_time, correct filtering, and matching hashes cannot prove it. If a future bit $`B`$ decides that only $`d_B`$ of two long-existing old documents is included, and the selected document is given an early knowledge time, the model outputting its index equals $`B`$. The log program may factor completely through the record projection, yet this projection itself is no longer $`ℱ_t`$-measurable.

Freezing the current code hash serves reproducibility; it does not prove that the rule was available at the time, nor does it rule out that the rule was chosen on the basis of future performance. A strong claim about a historical strategy/model needs evidence that the rule was already determined at the time or that its selection was historically adapted; a reference pipeline written today can prove how a fixed conditional comparator computes, not that it was deployed in the past. The member selection, metadata, and core of the deletion comparator $`D_{\rm del}`$ must likewise be adapted; deleting only truly late-arriving content does not supply this premise.

**Measurability and historical constructibility must not be conflated.** In a probability space that sets some text to be a constant, that text is mathematically $`ℱ_t`$-measurable for every $`t`$ even if it was actually published only in the future. A realized checkpoint fixed after the fact can also be treated as a constant function; this is not evidence of historical availability. PNI4 only transfers measurability within a given information model; it does not prove that every version actually used satisfies source admissibility, that the output could already be computed at the time, or that the strategy was deployed. The research must fix the algorithm and the cross-world objects in advance, record the real versions, selections, and replayable dependency sources, and then interpret the corresponding information set; one cannot, after seeing the future, rename all realized values as constants and declare no leakage.

## 8. PNI5: the correct definition of exogenous randomness

Let $`Z`$ be the future data that the research must exclude from additional reading. A sufficient condition is that the random source be independent of the whole data world; a weaker condition, specific to a fixed $`t`$, is

```math
\Omega\ \perp\!\!\!\perp\ Z\mid ℱ_t. \qquad (8.1)
```

**Proposition PNI5.** Under the conditions of PNI4, together with the conditional independence above, $`Y_t\perp\!\!\!\perp Z\mid ℱ_t`$. This means that, beyond the historically known information, the exogenous random computation carries no additional $`Z`$; it does not deny that history itself has predictive power for the future.

**Proof.** For bounded measurable $`a,b`$, $`a(Y_t)=a(G(H_t,C_t,\Omega))`$ is a function measurable with respect to $`\Omega`$ and $`ℱ_t`$. Conditional independence gives

```math
E[a(Y_t)b(Z)\mid ℱ_t]=E[a(Y_t)\mid ℱ_t]E[b(Z)\mid ℱ_t]. \qquad (8.2)
```

One can first verify this identity for functions that are piecewise constant in history and indicators of random-source events, and then extend it to the measurable functions above by the bounded monotone class theorem; or use directly the closure of conditional independence under measurable transformations, whose premise is exactly that the historical quantities are measurable. This identity is the definition of the stated conditional independence. ∎

**Marginal independence is not enough.** Let the historical bit $`H`$ and the future bit $`B`$ be independent and each uniform, and set $`\Omega=H\oplus B`$. Then $`\Omega`$ and $`B`$ are marginally independent, yet $`Y=H\oplus\Omega=B`$; the seed and the history together leak exactly the future. Hence the shorthand "the seed is independent of future data" in the original [T1.1](notes.md) must be tightened to independence from the whole data world or the conditional independence above, and cannot be read as marginal independence only. This clarification is also synced into the main notes; this file records the full reasoning and does not modify other files.

`seed=130` is an explicit fixed control value, convenient for repeated runs; its numerical value by itself does not prove that it was not tuned on the future. `seed=len(full_log)`, taking the seed from the final file hash, and testing many seeds and picking the one with the best future performance are not exogenous mechanisms. If only distributional non-interference is claimed, the conditional random kernel should also be fixed; "random numbers were used" does not automatically remove future information.

## 9. PNI6: perfect record non-interference may still fail to identify the clean statistic

Let the observable log and all submitted evidence be $`O`$, and let the set of true-availability worlds compatible with it, $`𝒲(O)`$, be nonempty. Each world $`w`$ has a bounded clean-comparator statistic $`S_{\rm clean}(w)\in[0,1]`$. Consider deterministic procedures that read only $`O`$ and output a closed interval $`I(O)=[\ell(O),u(O)]`$.

**Proposition PNI6.** If the procedure is required to be sound for all compatible worlds, i.e. $`S_{\rm clean}(w)\in I(O)`$ for every $`w\in 𝒲(O)`$, then

```math
\left[\inf_{w\in 𝒲(O)}S_{\rm clean}(w),\ \sup_{w\in 𝒲(O)}S_{\rm clean}(w)\right]\subseteq I(O) \qquad (9.1)
```

The infimum and supremum are finite; the inclusion of the endpoints in the conclusion uses the assumption that the output is a closed interval.

**Proof.** Soundness requires the interval to contain every compatible value. The lower end of the interval cannot exceed the infimum of these values, and the upper end cannot be less than the supremum; a closed interval also contains limiting endpoints, which gives the result. ∎

**An explicit two-world construction.** Take cutoff=1; the same document is observed, with the record claiming record_time=knowledge_time=0, and the text and all hashes identical. The true allowed availability time has not been certified. In world $`w_0`$ the document's true availability time is 0; in world $`w_1`$ it is actually 2, and the log's declaration was wrongly back-filled. Fix the training rule "predict 1 if the set is nonempty, otherwise predict 0", fix one test point with true label 1, and let the statistic be accuracy. Defining the clean set by true availability, $`w_0`$ includes the document and $`S_{\rm clean}=1`$; $`w_1`$ excludes it and $`S_{\rm clean}=0`$. The record projections are identical in the two worlds, and any procedure that works strictly from the record projection can perfectly satisfy PNI1–PNI3, but any deterministic interval sound for both worlds must contain $`[0,1]`$.

This example deliberately allows the knowledge-time declaration to be wrong; what it violates is **the authenticity contract for per-version historical source admissibility**, and one cannot conclude from it that $`H_t`$ is mathematically non-measurable: in the probability space consisting of only these two worlds, the same observation $`O`$ and its $`H_t`$ are constants and hence necessarily measurable. So it is not a counterexample to PNI4; it shows that record non-interference, informational measurability, true source admissibility, and identification of the clean comparator are different obligations. An uncertified log cannot prove the latter two by itself. Only if reliable evidence of true knowledge times covering all fields and selections has been obtained will the set of compatible worlds shrink, so that a narrower conclusion might be possible. Running more future-append tests alone cannot shrink these real worlds.

If a randomized confidence procedure is used, the randomness and the coverage quantifiers must be defined separately, and the deterministic necessary condition above cannot be applied directly. However, when the two worlds give exactly the same observation distribution and coverage of 0 and of 1 are each required with probability at least $`1-\alpha`$, the union bound still requires the procedure to contain both simultaneously with probability at least $`1-2\alpha`$; this also shows that, without new identifying information, randomization cannot in general produce sound narrow intervals. This observation neither uses nor replaces later real audit designs.

## 10. What tests can confirm, interface acceptance, and open premises

**Finite tests do not constitute a general proof.** When the space of valid events is infinite, for any given finite set of tests one can construct a program that agrees with the correct program on all tested inputs but flips the stable output on an untested combination of future event_id/payload. Finite observation cannot distinguish the two. If the input universe and the program semantics really are finite and all relevant input pairs have been enumerated, one can prove properties of that finite model; they cannot be extrapolated to properties of unmodelled files, environments, or real sources.

The tests suited to the reference pipeline are adversarial checks of the construction: future additions, same-ID revisions, tombstones, label/source/core changes, future deduplication bridges, high-frequency words in a future vocabulary, effects of future counts, random-stream consumption, future validation labels, and hyperparameter selection; check all intermediate stable artifacts and the canonical bytes of the stable output. Also needed: cutoff boundaries, deterministic ordering for equal knowledge times, empty history, rejection of bad visible payloads, opaque bad future payloads under the valid-header contract, and equivalence of different physical orders with the same history. These verify concrete implementation branches and do not replace the closed-dependency assumption of PNI3.

The suggested implementation interface is:

1. `canonical_history(events, cutoff)`: valid-header projection, then validation of visible payloads only; outputs a canonical history object bound to the cutoff.
2. `replay_visible(history, cutoff)`: replays full versions/tombstones by knowledge time; all downstream components receive only this history and the fixed configuration, and no longer receive a handle to the full log.
3. `stable_pipeline(history, config, seed, cutoff)`: filtering, vocabulary, deduplication, sampling, splitting, and development selection in sequence, each outputting a reviewable stable artifact. The exogenous/historical availability of config is part of the calling contract.
4. `audit_envelope(full_input, environment, diagnostics)`: records the full file identity and run information, stored separately, with no flow back.

| Proof obligation | Status and where closed | Real-world claims not included |
|---|---|---|
| Constant on history fibres and factorization | CLOSED-LOCAL, PNI1 | Does not verify the true times of records |
| Equivalence conditions between appends and non-interference | CLOSED-LOCAL, PNI2 and the reachability counterexample | Does not guarantee closure for arbitrary physical log domains |
| Visible-version replay and component composition | CLOSED-LOCAL, PNI3 | Does not prove that arbitrary third-party programs have no hidden inputs |
| Transfer of true point-in-time measurability | CLOSED-LOCAL, PNI4, with the external adaptedness assumption made explicit | Does not prove that sources, selection, and code were historically available |
| Exogenous randomness adds no future information | CLOSED-LOCAL, PNI5 | Does not guarantee that picking a seed after the fact is valid |
| Necessary interval width under unidentified ground truth | CLOSED-LOCAL, PNI6 | Not a new statistical optimality or original result |

All six conditional mathematical obligations have local proofs; the authenticity of real times, complete version logs, historical selection, and external dependencies remains open. This file did not run any new checker/training and produced no computational results or records of additional compute use. An internal review can check the formulas and quantifiers. After a later implementation passes finite tests, the reasonable conclusion is "a PIT construction and checks of its implementation under the specified interface and input contract", not "the absence of leakage in actual history has been proved".
