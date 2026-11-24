"""Offline WP0.2 synthetic smoke study; not a real-language benchmark."""
import hashlib
import json
import platform
import re
import time
from pathlib import Path

import numpy as np
import torch
from torch import nn
from torch.nn import functional as F

from research.local.world import generate, digest
from research.evaluation.evaluate import cluster_bootstrap, LABELS

CONFIG = dict(data_seed=20261115, seeds=[11,23,47], companies=30, quarters=20,
              train_quarters=16, steps=250, lr=0.02, embedding_dim=24, hidden_dim=32,
              permission_weight=0.2, margin=0.5, bootstrap_repetitions=2000,
              cpu_threads=1)


def tokens(text):
    # A declared tiny vocabulary, not a claim of a general financial parser.
    return re.findall(r'[a-z]+|[0-9]+|[^\w\s]', text.lower())


class Classifier(nn.Module):
    def __init__(self, vocab_size):
        super().__init__()
        self.embed = nn.Embedding(vocab_size, CONFIG['embedding_dim'], padding_idx=0)
        self.head = nn.Sequential(nn.Linear(CONFIG['embedding_dim'],CONFIG['hidden_dim']),
                                  nn.Tanh(),nn.Linear(CONFIG['hidden_dim'],3))

    def forward(self, ids):
        mask = (ids!=0).unsqueeze(-1)
        mean = (self.embed(ids)*mask).sum(1)/mask.sum(1).clamp(min=1)
        return self.head(mean)


def vectorize(texts, vocab):
    words = [[vocab.get(t,1) for t in tokens(s)] for s in texts]
    width = max(map(len,words))
    return torch.tensor([w+[0]*(width-len(w)) for w in words],dtype=torch.long)


def loss_permissions(za, zb, y0, y1, kinds):
    result = za.sum()*0
    p, q = za.softmax(-1), zb.softmax(-1)
    for kind in range(3):
        use = kinds == kind
        if not use.any():
            continue
        if kind == 0:  # symmetric distribution matching, not label matching
            l = 0.5*((p[use]*(za[use].log_softmax(-1)-zb[use].log_softmax(-1))).sum(-1)+
                     (q[use]*(zb[use].log_softmax(-1)-za[use].log_softmax(-1))).sum(-1))
        elif kind == 1:
            # Encourage edited prediction to retain the original modal class.
            winner = za[use].detach().argmax(-1)
            keep = zb[use].gather(1,winner[:,None]).squeeze(1)
            others = zb[use].masked_fill(F.one_hot(winner,3).bool(),-torch.inf).max(-1).values
            l = F.relu(CONFIG['margin'] + others - keep)
        else:
            a,b = y0[use],y1[use]
            z0,z1=za[use],zb[use]
            change=(z1.gather(1,b[:,None])-z1.gather(1,a[:,None])-
                    z0.gather(1,b[:,None])+z0.gather(1,a[:,None])).squeeze(1)
            l = F.relu(CONFIG['margin'] - change)
        result = result + l.sum()/len(za)
    return result


def main():
    started=time.perf_counter()
    torch.set_num_threads(CONFIG['cpu_threads'])
    torch.use_deterministic_algorithms(True)
    rows=generate(seed=CONFIG['data_seed'],companies=CONFIG['companies'],quarters=CONFIG['quarters'])
    train=[d for d in rows if d['quarter'] < CONFIG['train_quarters']]
    test=[d for d in rows if d['quarter'] >= CONFIG['train_quarters']]
    pairs=[(d,e,i) for d in train for i,e in enumerate(d['edits'][:3])]
    vocabulary=sorted({t for d in train for s in [d['text']]+[e['text'] for e in d['edits'][:3]] for t in tokens(s)})
    vocab={word:i+2 for i,word in enumerate(vocabulary)}
    originals=vectorize([d['text'] for d in train],vocab)
    original_y=torch.tensor([d['stance'] for d in train])
    xa=vectorize([d['text'] for d,e,i in pairs],vocab)
    xb=vectorize([e['text'] for d,e,i in pairs],vocab)
    ya=torch.tensor([d['stance'] for d,e,i in pairs]); yb=torch.tensor([e['stance'] for d,e,i in pairs])
    kinds=torch.tensor([i for d,e,i in pairs])
    xt=vectorize([d['text'] for d in test],vocab)
    all_predictions={}; results=[]; determinism={}
    def train_one(seed,mode):
        torch.manual_seed(seed)
        model=Classifier(len(vocab)+2)
        optimizer=torch.optim.Adam(model.parameters(),lr=CONFIG['lr'])
        permutation=torch.randperm(len(kinds),generator=torch.Generator().manual_seed(seed+1000))
        for step in range(CONFIG['steps']):
            optimizer.zero_grad(set_to_none=True)
            if mode=='original_ce':
                loss=F.cross_entropy(model(originals),original_y)
            else:
                a,b=model(xa),model(xb)
                loss=0.5*(F.cross_entropy(a,ya)+F.cross_entropy(b,yb))
                if mode!='edited_ce':
                    types=kinds[permutation] if mode=='shuffled_permissions' else kinds
                    loss=loss+CONFIG['permission_weight']*loss_permissions(a,b,ya,yb,types)
            loss.backward(); optimizer.step()
        return model
    for seed in CONFIG['seeds']:
        for mode in ['original_ce','edited_ce','permissions','shuffled_permissions']:
            tick=time.perf_counter(); model=train_one(seed,mode); model.eval()
            weight_hash=hashlib.sha256(b''.join(v.detach().numpy().tobytes() for v in model.state_dict().values())).hexdigest()
            if seed==CONFIG['seeds'][0] and mode=='permissions':
                rerun=train_one(seed,mode)
                determinism=dict(seed=seed,mode=mode,bitwise_equal=all(torch.equal(v,rerun.state_dict()[key]) for key,v in model.state_dict().items()))
            with torch.no_grad():
                logits=model(xt); pred=logits.argmax(-1).numpy(); p=logits.softmax(-1)
                violations={}
                for j,name in enumerate(['INV','LBL','REL']):
                    out=model(vectorize([d['edits'][j]['text'] for d in test],vocab)); q=out.softmax(-1)
                    if name=='INV':
                        flags=(0.5*(p-q).abs().sum(-1)>0.05).numpy()
                    elif name=='LBL':
                        flags=(out.argmax(-1)!=logits.argmax(-1)).numpy()
                    else:
                        a=torch.tensor([d['stance'] for d in test]); b=torch.tensor([d['edits'][j]['stance'] for d in test])
                        shift=(out.gather(1,b[:,None])-out.gather(1,a[:,None])-
                               logits.gather(1,b[:,None])+logits.gather(1,a[:,None])).squeeze(1)
                        flags=(shift < CONFIG['margin']).numpy()
                    # Company blocks preserve generated within-company temporal dependence.
                    company_flags=np.array([flags[[d['company']==c for d in test]].mean() for c in range(CONFIG['companies'])])
                    rng=np.random.default_rng(seed)
                    boot=company_flags[rng.integers(0,len(company_flags),(2000,len(company_flags)))].mean(1)
                    violations[name]=dict(estimate=float(flags.mean()),lower=float(np.quantile(boot,.025)),upper=float(np.quantile(boot,.975)),
                                          method='company cluster percentile bootstrap; approximate')
            all_predictions[(seed,mode)]=pred
            records=[dict(id=d['id'],family_id=d['family'],event_id=f"company{d['company']}",label=LABELS[d['stance']],prediction=LABELS[int(pred[i])]) for i,d in enumerate(test)]
            if mode!='original_ce':
                baseline=all_predictions[(seed,'original_ce')]
                for i,r in enumerate(records): r['baseline_prediction']=LABELS[int(baseline[i])]
            summary=cluster_bootstrap(records,CONFIG['bootstrap_repetitions'],seed)
            results.append(dict(seed=seed,mode=mode,parameter_count=sum(v.numel() for v in model.parameters()),
                                weights_sha256=weight_hash,elapsed_seconds=time.perf_counter()-tick,
                                metrics=summary,permission_violations=violations))
            print(seed,mode,'macro_f1',summary['systems']['prediction']['macro_f1'],flush=True)
    # Main causal contrast is permissions vs edited CE on identical edit exposures.
    paired=[]
    for seed in CONFIG['seeds']:
        records=[dict(id=d['id'],family_id=d['family'],event_id=f"company{d['company']}",label=LABELS[d['stance']],
                      prediction=LABELS[int(all_predictions[(seed,'permissions')][i])],
                      baseline_prediction=LABELS[int(all_predictions[(seed,'edited_ce')][i])]) for i,d in enumerate(test)]
        paired.append(dict(seed=seed,comparison='permissions_minus_edited_ce',result=cluster_bootstrap(records,2000,seed)))
    output=dict(config=CONFIG,data_sha256=digest(rows),hardware=platform.processor(),platform=platform.platform(),
                python=platform.python_version(),torch=torch.__version__,numpy=np.__version__,
                train_families=len(train),test_families=len(test),inference_clusters=CONFIG['companies'],
                vocabulary_source='training families and their edits only; unknown token for unseen tokens',
                determinism=determinism,results=results,paired_main_contrast=paired,elapsed_seconds=time.perf_counter()-started,
                limitations=['synthetic grammar with explicit stance verbs; not real data',
                             'small mean-embedding classifier, not 24M transformer or pretrained LM',
                             'company clusters assumed independent, percentile CI is not a certificate',
                             'no model tuning or selection on test; single prespecified configuration',
                             'UP applies only to metric axis and is not included in stance loss',
                             '3 seeds characterize this setup, not universal effectiveness'])
    out=Path('research/experiments/local_foundations/results.json')
    out.write_text(json.dumps(output,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8')
    print('elapsed_seconds',output['elapsed_seconds'],'bitwise_repeat',determinism,flush=True)


if __name__=='__main__': main()
