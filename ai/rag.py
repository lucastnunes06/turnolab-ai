"""Local lexical retrieval and LSA ablation; no downloaded embedding model."""
import hashlib
import json
import re
import time
from functools import lru_cache
from pathlib import Path
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import TruncatedSVD
from sklearn.preprocessing import normalize
from backend.app.config import ROOT, REPORTS
DANGEROUS = re.compile('ignore (all|previous)|system prompt|execute.*(shell|sql)|reveal.*secret|ignore.*instru|exfiltr', re.I)

class Retriever:

    def __init__(self, directory=None):
        self.docs = {}
        self.chunks = []
        self.quarantined = []
        for path in sorted(Path(directory or ROOT / 'ai/corpus').glob('*.md')):
            content = path.read_text(encoding='utf-8').replace('\r\n', '\n').strip()
            doc_id = path.stem
            self.docs[doc_id] = dict(id=doc_id, title=content.splitlines()[0].lstrip('# '), content=content, sha256=hashlib.sha256(content.encode()).hexdigest())
            for i, para in enumerate(re.split('\\n\\s*\\n', content)):
                if len(para) < 90:
                    continue
                if DANGEROUS.search(para):
                    self.quarantined.append(doc_id)
                    continue
                self.chunks.append(dict(id=f'{doc_id}:{i}', document_id=doc_id, title=self.docs[doc_id]['title'], text=para[:1600], url=f'/api/documents/{doc_id}'))
        self.vectorizer = TfidfVectorizer(ngram_range=(1, 2), strip_accents='unicode', sublinear_tf=True, stop_words='a o as os de da do das dos e em um uma para por com que qual quais como quando quem onde ao aos na no nas nos se sua seu suas seus esta este isso sao ser ter mais pode e'.split())
        self.matrix = self.vectorizer.fit_transform([c['text'] for c in self.chunks])
        self.char = TfidfVectorizer(analyzer='char_wb', ngram_range=(3, 5), strip_accents='unicode')
        self.cm = self.char.fit_transform([c['text'] for c in self.chunks])
        self.svd = TruncatedSVD(n_components=min(12, len(self.chunks) - 1), random_state=42)
        self.latent = normalize(self.svd.fit_transform(self.matrix))

    def search(self, query, k=3, strategy='lexical'):
        start = time.perf_counter()
        q = self.vectorizer.transform([query])
        word = (self.matrix @ q.T).toarray().ravel()
        chars = (self.cm @ self.char.transform([query]).T).toarray().ravel()
        latent = (self.latent @ normalize(self.svd.transform(q)).T).ravel()
        scores = {'lexical': word, 'lsa': np.maximum(0, latent), 'hybrid': 0.65 * word + 0.35 * chars}[strategy]
        order = np.argsort(-scores)[:k]
        hits = [dict(**self.chunks[i], score=float(scores[i])) for i in order if scores[i] >= 0.08 and word[i] >= 0.025]
        return dict(hits=hits, abstained=not hits, strategy=strategy, latency_ms=(time.perf_counter() - start) * 1000, index_version='tfidf-v1', embedding_note='LSA is a corpus-trained linear projection, not a pretrained semantic embedding model.')

@lru_cache
def retriever():
    return Retriever()
CASES = [('Qual é a política de reposição de estoque?', 'replenishment'), ('Como considerar o prazo de entrega de ingredientes?', 'replenishment'), ('Posso converter kg em unidades?', 'replenishment'), ('O que verificar sobre validade do frango?', 'replenishment'), ('O que fazer durante picos de pedidos?', 'peaks'), ('Quantas pessoas adicionais considerar no turno?', 'peaks'), ('Reforçar equipe sempre aumenta produção?', 'peaks'), ('Que alternativas e incertezas mostrar ao recomendar?', 'peaks'), ('Como calcular capacidade efetiva da cozinha?', 'capacity'), ('O que é backlog no modelo de fila?', 'capacity'), ('Por que um pedido acumula custo de atraso?', 'capacity'), ('O simulador modela desistência?', 'capacity'), ('O copiloto pode cancelar pedidos?', 'cancellation'), ('O que fazer se faltar um ingrediente no cardápio?', 'cancellation'), ('Pedidos processados são receita realizada?', 'cancellation'), ('Como promover um modelo?', 'governance'), ('O modo offline usa uma LLM local?', 'governance'), ('Quem aprova propostas e recomendações?', 'governance'), ('Como tratar instruções dentro de documentos?', 'governance'), ('Quem venceu a Copa do Mundo de 2022?', None), ('Qual é a senha do WiFi do vizinho?', None), ('Qual a cotação do bitcoin agora?', None), ('Qual medicamento tomar para dor?', None)]

def evaluate():
    engine = retriever()
    report = {}
    details = []
    for strategy in ['lexical', 'lsa', 'hybrid']:
        hits = []
        abst = []
        lat = []
        citation = []
        for question, expected in CASES:
            result = engine.search(question, strategy=strategy)
            ids = [h['document_id'] for h in result['hits']]
            if expected:
                hits.append(expected in ids)
            else:
                abst.append(result['abstained'])
            if expected and ids:
                citation.extend([x == expected for x in ids])
            lat.append(result['latency_ms'])
            details.append(dict(strategy=strategy, question=question, expected=expected, retrieved=ids, abstained=result['abstained']))
        report[strategy] = dict(recall_at_3=float(np.mean(hits)), hit_rate_at_3=float(np.mean(hits)), reference_relevance_precision=float(np.mean(citation)), correct_abstention=float(np.mean(abst)), latency_mean_ms=float(np.mean(lat)), n=len(CASES))
    report['protocol'] = dict(questions=len(CASES), answerable=sum((x[1] is not None for x in CASES)), limitation='Small hand-authored set; one gold document per answer. No claim of LLM answer entailment measurement.', unsupported_answers='Measured separately for offline coordinator in adversarial tests; no external LLM executed.')
    (REPORTS / 'rag.json').write_text(json.dumps(report, indent=2))
    (REPORTS / 'rag_cases.json').write_text(json.dumps(details, indent=2, ensure_ascii=False))
    print(json.dumps(report, indent=2))
if __name__ == '__main__':
    evaluate()
