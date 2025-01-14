import pytest
import math
from unittest.mock import patch

from haystack.schema import Document
from haystack.nodes.ranker.base import BaseRanker
from haystack.nodes.ranker import SentenceTransformersRanker, CohereRanker
from haystack.errors import HaystackError


@pytest.fixture
def docs():
    docs = [
        Document(
            content="""Aaron Aaron ( or ; ""Ahärôn"") is a prophet, high priest, and the brother of Moses in the Abrahamic religions. Knowledge of Aaron, along with his brother Moses, comes exclusively from religious texts, such as the Bible and Quran. The Hebrew Bible relates that, unlike Moses, who grew up in the Egyptian royal court, Aaron and his elder sister Miriam remained with their kinsmen in the eastern border-land of Egypt (Goshen). When Moses first confronted the Egyptian king about the Israelites, Aaron served as his brother's spokesman (""prophet"") to the Pharaoh. Part of the Law (Torah) that Moses received from""",
            meta={"name": "0"},
            id="1",
        ),
        Document(
            content="""Democratic Republic of the Congo to the south. Angola's capital, Luanda, lies on the Atlantic coast in the northwest of the country. Angola, although located in a tropical zone, has a climate that is not characterized for this region, due to the confluence of three factors: As a result, Angola's climate is characterized by two seasons: rainfall from October to April and drought, known as ""Cacimbo"", from May to August, drier, as the name implies, and with lower temperatures. On the other hand, while the coastline has high rainfall rates, decreasing from North to South and from to , with""",
            id="2",
        ),
        Document(
            content="""Schopenhauer, describing him as an ultimately shallow thinker: ""Schopenhauer has quite a crude mind ... where real depth starts, his comes to an end."" His friend Bertrand Russell had a low opinion on the philosopher, and attacked him in his famous ""History of Western Philosophy"" for hypocritically praising asceticism yet not acting upon it. On the opposite isle of Russell on the foundations of mathematics, the Dutch mathematician L. E. J. Brouwer incorporated the ideas of Kant and Schopenhauer in intuitionism, where mathematics is considered a purely mental activity, instead of an analytic activity wherein objective properties of reality are""",
            meta={"name": "1"},
            id="3",
        ),
        Document(
            content="""The Dothraki vocabulary was created by David J. Peterson well in advance of the adaptation. HBO hired the Language Creatio""",
            meta={"name": "2"},
            id="4",
        ),
        Document(
            content="""The title of the episode refers to the Great Sept of Baelor, the main religious building in King's Landing, where the episode's pivotal scene takes place. In the world created by George R. R. Martin""",
            meta={},
            id="5",
        ),
    ]
    return docs


@pytest.fixture
def mock_cohere_post():
    class Response:
        def __init__(self, text: str):
            self.text = text

    with patch("haystack.nodes.ranker.cohere.CohereRanker._post") as cohere_post:
        cohere_post.return_value = Response(
            text='{"id":"73701fd4-fe30-4007-9698-e960a51b19b4","results":[{"index":4,"relevance_score":0.9937345},{"index":3,"relevance_score":0.2232077},{"index":0,"relevance_score":0.006538825},{"index":2,"relevance_score":0.002278331},{"index":1,"relevance_score":0.000035633544}],"meta":{"api_version":{"version":"1"}}}'
        )
        yield cohere_post


@pytest.mark.unit
def test_ranker_preprocess_batch_queries_and_docs_raises():
    query_1 = "query 1"
    query_2 = "query 2"
    docs = [Document(content="dummy doc 1")]
    with patch("haystack.nodes.ranker.sentence_transformers.SentenceTransformersRanker.__init__") as mock_ranker_init:
        mock_ranker_init.return_value = None
        ranker = SentenceTransformersRanker(model_name_or_path="fake_model")
    with pytest.raises(HaystackError, match="Number of queries must be 1 if a single list of Documents is provided."):
        _, _, _, _ = ranker._preprocess_batch_queries_and_docs(queries=[query_1, query_2], documents=docs)


@pytest.mark.unit
def test_ranker_preprocess_batch_queries_and_docs_single_query_single_doc_list():
    query1 = "query 1"
    docs1 = [Document(content="dummy doc 1"), Document(content="dummy doc 2")]
    with patch("haystack.nodes.ranker.sentence_transformers.SentenceTransformersRanker.__init__") as mock_ranker_init:
        mock_ranker_init.return_value = None
        ranker = SentenceTransformersRanker(model_name_or_path="fake_model")
    num_of_docs, all_queries, all_docs, single_list_of_docs = ranker._preprocess_batch_queries_and_docs(
        queries=[query1], documents=docs1
    )
    assert single_list_of_docs is True
    assert num_of_docs == [2]
    assert len(all_queries) == 2
    assert len(all_docs) == 2


@pytest.mark.unit
def test_ranker_preprocess_batch_queries_and_docs_multiple_queries_multiple_doc_lists():
    query_1 = "query 1"
    query_2 = "query 2"
    docs1 = [Document(content="dummy doc 1"), Document(content="dummy doc 2")]
    docs2 = [Document(content="dummy doc 3")]
    with patch("haystack.nodes.ranker.sentence_transformers.SentenceTransformersRanker.__init__") as mock_ranker_init:
        mock_ranker_init.return_value = None
        ranker = SentenceTransformersRanker(model_name_or_path="fake_model")
    num_of_docs, all_queries, all_docs, single_list_of_docs = ranker._preprocess_batch_queries_and_docs(
        queries=[query_1, query_2], documents=[docs1, docs2]
    )
    assert single_list_of_docs is False
    assert num_of_docs == [2, 1]
    assert len(all_queries) == 3
    assert len(all_docs) == 3


@pytest.mark.unit
def test_ranker_get_batches():
    all_queries = ["query 1", "query 1"]
    all_docs = [Document(content="dummy doc 1"), Document(content="dummy doc 2")]
    batches = SentenceTransformersRanker._get_batches(all_queries=all_queries, all_docs=all_docs, batch_size=None)
    assert next(batches) == (all_queries, all_docs)

    batches = SentenceTransformersRanker._get_batches(all_queries=all_queries, all_docs=all_docs, batch_size=1)
    assert next(batches) == (all_queries[0:1], all_docs[0:1])


def test_ranker(ranker, docs):
    query = "What is the most important building in King's Landing that has a religious background?"
    results = ranker.predict(query=query, documents=docs)
    assert results[0] == docs[4]


def test_ranker_batch_single_query_single_doc_list(ranker, docs):
    query = "What is the most important building in King's Landing that has a religious background?"
    results = ranker.predict_batch(queries=[query], documents=docs)
    assert results[0] == docs[4]


def test_ranker_batch_single_query_multiple_doc_lists(ranker, docs):
    query = "What is the most important building in King's Landing that has a religious background?"
    results = ranker.predict_batch(queries=[query], documents=[docs, docs])
    assert isinstance(results, list)
    assert isinstance(results[0], list)
    for reranked_docs in results:
        assert reranked_docs[0] == docs[4]


def test_ranker_batch_multiple_queries_multiple_doc_lists(ranker, docs):
    query_1 = "What is the most important building in King's Landing that has a religious background?"
    query_2 = "How is Angola's climate characterized?"
    results = ranker.predict_batch(queries=[query_1, query_2], documents=[docs, docs])
    assert isinstance(results, list)
    assert isinstance(results[0], list)
    assert results[0][0] == docs[4]
    assert results[1][0] == docs[1]


def test_ranker_two_logits(ranker_two_logits, docs):
    assert isinstance(ranker_two_logits, BaseRanker)
    assert isinstance(ranker_two_logits, SentenceTransformersRanker)
    query = "Welches ist das wichtigste Gebäude in Königsmund, das einen religiösen Hintergrund hat?"
    docs = [
        Document(
            content="""Aaron Aaron (oder ; "Ahärôn") ist ein Prophet, Hohepriester und der Bruder von Moses in den abrahamitischen Religionen. Aaron ist ebenso wie sein Bruder Moses ausschließlich aus religiösen Texten wie der Bibel und dem Koran bekannt. Die hebräische Bibel berichtet, dass Aaron und seine ältere Schwester Mirjam im Gegensatz zu Mose, der am ägyptischen Königshof aufwuchs, bei ihren Verwandten im östlichen Grenzland Ägyptens (Goschen) blieben. Als Mose den ägyptischen König zum ersten Mal mit den Israeliten konfrontierte, fungierte Aaron als Sprecher ("Prophet") seines Bruders gegenüber dem Pharao. Ein Teil des Gesetzes (Tora), das Mose von""",
            meta={"name": "0"},
            id="1",
        ),
        Document(
            content="""Demokratische Republik Kongo im Süden. Die angolanische Hauptstadt Luanda liegt an der Atlantikküste im Nordwesten des Landes. Angola liegt zwar in einer tropischen Zone, hat aber ein Klima, das aufgrund des Zusammenwirkens von drei Faktoren nicht für diese Region typisch ist: So ist das Klima Angolas durch zwei Jahreszeiten gekennzeichnet: Regenfälle von Oktober bis April und die als "Cacimbo" bezeichnete Dürre von Mai bis August, die, wie der Name schon sagt, trockener ist und niedrigere Temperaturen aufweist. Andererseits sind die Niederschlagsmengen an der Küste sehr hoch und nehmen von Norden nach Süden und von Süden nach Süden ab, mit""",
            id="2",
        ),
        Document(
            content="""Schopenhauer, indem er ihn als einen letztlich oberflächlichen Denker beschreibt: ""Schopenhauer hat einen ziemlich groben Verstand ... wo wirkliche Tiefe beginnt, hört seine auf."" Sein Freund Bertrand Russell hatte eine schlechte Meinung von dem Philosophen und griff ihn in seiner berühmten "Geschichte der westlichen Philosophie" an, weil er heuchlerisch die Askese lobte, aber nicht danach handelte. Der holländische Mathematiker L. E. J. Brouwer, der auf der gegenüberliegenden Insel von Russell über die Grundlagen der Mathematik sprach, nahm die Ideen von Kant und Schopenhauer in den Intuitionismus auf, in dem die Mathematik als eine rein geistige Tätigkeit betrachtet wird und nicht als eine analytische Tätigkeit, bei der die objektiven Eigenschaften der Realität berücksichtigt werden.""",
            meta={"name": "1"},
            id="3",
        ),
        Document(
            content="""Das dothrakische Vokabular wurde von David J. Peterson lange vor der Verfilmung erstellt. HBO beauftragte das Language Creatio""",
            meta={"name": "2"},
            id="4",
        ),
        Document(
            content="""Der Titel der Episode bezieht sich auf die Große Septe von Baelor, das wichtigste religiöse Gebäude in Königsmund, in dem die Schlüsselszene der Episode stattfindet. In der von George R. R. Martin geschaffenen Welt""",
            meta={},
            id="5",
        ),
    ]
    results = ranker_two_logits.predict(query=query, documents=docs)
    assert results[0] == docs[4]


def test_ranker_returns_normalized_score(ranker):
    query = "What is the most important building in King's Landing that has a religious background?"

    docs = [
        Document(
            content="""Aaron Aaron ( or ; ""Ahärôn"") is a prophet, high priest, and the brother of Moses in the Abrahamic religions. Knowledge of Aaron, along with his brother Moses, comes exclusively from religious texts, such as the Bible and Quran. The Hebrew Bible relates that, unlike Moses, who grew up in the Egyptian royal court, Aaron and his elder sister Miriam remained with their kinsmen in the eastern border-land of Egypt (Goshen). When Moses first confronted the Egyptian king about the Israelites, Aaron served as his brother's spokesman (""prophet"") to the Pharaoh. Part of the Law (Torah) that Moses received from""",
            meta={"name": "0"},
            id="1",
        )
    ]

    results = ranker.predict(query=query, documents=docs)
    score = results[0].score
    precomputed_score = 5.8796231e-05
    assert math.isclose(precomputed_score, score, rel_tol=0.01)


def test_ranker_returns_raw_score_when_no_scaling():
    ranker = SentenceTransformersRanker(model_name_or_path="cross-encoder/ms-marco-MiniLM-L-12-v2", scale_score=False)
    query = "What is the most important building in King's Landing that has a religious background?"

    docs = [
        Document(
            content="""Aaron Aaron ( or ; ""Ahärôn"") is a prophet, high priest, and the brother of Moses in the Abrahamic religions. Knowledge of Aaron, along with his brother Moses, comes exclusively from religious texts, such as the Bible and Quran. The Hebrew Bible relates that, unlike Moses, who grew up in the Egyptian royal court, Aaron and his elder sister Miriam remained with their kinsmen in the eastern border-land of Egypt (Goshen). When Moses first confronted the Egyptian king about the Israelites, Aaron served as his brother's spokesman (""prophet"") to the Pharaoh. Part of the Law (Torah) that Moses received from""",
            meta={"name": "0"},
            id="1",
        )
    ]

    results = ranker.predict(query=query, documents=docs)
    score = results[0].score
    precomputed_score = -9.744687
    assert math.isclose(precomputed_score, score, rel_tol=0.001)


def test_ranker_returns_raw_score_for_two_logits(ranker_two_logits):
    query = "Welches ist das wichtigste Gebäude in Königsmund, das einen religiösen Hintergrund hat?"
    docs = [
        Document(
            content="""Aaron Aaron (oder ; "Ahärôn") ist ein Prophet, Hohepriester und der Bruder von Moses in den abrahamitischen Religionen. Aaron ist ebenso wie sein Bruder Moses ausschließlich aus religiösen Texten wie der Bibel und dem Koran bekannt. Die hebräische Bibel berichtet, dass Aaron und seine ältere Schwester Mirjam im Gegensatz zu Mose, der am ägyptischen Königshof aufwuchs, bei ihren Verwandten im östlichen Grenzland Ägyptens (Goschen) blieben. Als Mose den ägyptischen König zum ersten Mal mit den Israeliten konfrontierte, fungierte Aaron als Sprecher ("Prophet") seines Bruders gegenüber dem Pharao. Ein Teil des Gesetzes (Tora), das Mose von""",
            meta={"name": "0"},
            id="1",
        )
    ]

    results = ranker_two_logits.predict(query=query, documents=docs)
    score = results[0].score
    precomputed_score = -3.61354
    assert math.isclose(precomputed_score, score, rel_tol=0.001)


def test_predict_batch_returns_correct_number_of_docs(ranker):
    docs = [Document(content=f"test {number}") for number in range(5)]

    assert len(ranker.predict("where is test 3?", docs, top_k=4)) == 4

    assert len(ranker.predict_batch(["where is test 3?"], docs, batch_size=2, top_k=4)) == 4


@pytest.mark.unit
def test_cohere_ranker(docs, mock_cohere_post):
    query = "What is the most important building in King's Landing that has a religious background?"
    ranker = CohereRanker(api_key="fake_key", model_name_or_path="rerank-english-v2.0")
    results = ranker.predict(query=query, documents=docs)
    mock_cohere_post.assert_called_once_with(
        {
            "model": "rerank-english-v2.0",
            "query": query,
            "documents": [{"text": d.content} for d in docs],
            "top_n": None,  # By passing None we return all documents and use top_k to truncate later
            "return_documents": False,
            "max_chunks_per_doc": None,
        }
    )
    assert results[0] == docs[4]


@pytest.mark.unit
def test_cohere_ranker_batch_single_query_single_doc_list(docs, mock_cohere_post):
    query = "What is the most important building in King's Landing that has a religious background?"
    ranker = CohereRanker(api_key="fake_key", model_name_or_path="rerank-english-v2.0")
    results = ranker.predict_batch(queries=[query], documents=docs)
    mock_cohere_post.assert_called_once_with(
        {
            "model": "rerank-english-v2.0",
            "query": query,
            "documents": [{"text": d.content} for d in docs],
            "top_n": None,  # By passing None we return all documents and use top_k to truncate later
            "return_documents": False,
            "max_chunks_per_doc": None,
        }
    )
    assert results[0] == docs[4]


@pytest.mark.unit
def test_cohere_ranker_batch_single_query_multiple_doc_lists(docs, mock_cohere_post):
    query = "What is the most important building in King's Landing that has a religious background?"
    ranker = CohereRanker(api_key="fake_key", model_name_or_path="rerank-english-v2.0")
    results = ranker.predict_batch(queries=[query], documents=[docs, docs])
    assert mock_cohere_post.call_count == 2
    mock_cohere_post.assert_called_with(
        {
            "model": "rerank-english-v2.0",
            "query": query,
            "documents": [{"text": d.content} for d in docs],
            "top_n": None,  # By passing None we return all documents and use top_k to truncate later
            "return_documents": False,
            "max_chunks_per_doc": None,
        }
    )
    assert isinstance(results, list)
    assert isinstance(results[0], list)
    for reranked_docs in results:
        assert reranked_docs[0] == docs[4]


@pytest.mark.unit
def test_cohere_ranker_batch_multiple_queries_multiple_doc_lists(docs, mock_cohere_post):
    query = "What is the most important building in King's Landing that has a religious background?"
    ranker = CohereRanker(api_key="fake_key", model_name_or_path="rerank-english-v2.0")
    results = ranker.predict_batch(queries=[query, query], documents=[docs, docs])
    assert mock_cohere_post.call_count == 2
    mock_cohere_post.assert_called_with(
        {
            "model": "rerank-english-v2.0",
            "query": query,
            "documents": [{"text": d.content} for d in docs],
            "top_n": None,  # By passing None we return all documents and use top_k to truncate later
            "return_documents": False,
            "max_chunks_per_doc": None,
        }
    )
    assert isinstance(results, list)
    assert isinstance(results[0], list)
    assert results[0][0] == docs[4]
    assert results[1][0] == docs[4]
