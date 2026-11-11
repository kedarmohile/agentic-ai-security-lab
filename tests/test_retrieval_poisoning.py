from agentic_ai_security_lab.retrieval_poisoning import (
    EXPECTED_ANSWER,
    POISON_DOC_ID,
    POISON_MARKER,
    POISON_TEXT,
    QUERY,
    TRUSTED_DOC_ID,
    DeterministicRagPipeline,
    Document,
    InMemoryCorpus,
    LabMode,
    LexicalRetriever,
    PipelineMode,
    SourceTrust,
    Verdict,
    run_retrieval_poisoning_lab,
)


def test_baseline_control_returns_trusted_answer() -> None:
    result = run_retrieval_poisoning_lab(
        mode=LabMode.BASELINE,
        run_id="test-baseline",
    )

    assert result.baseline_control_correct is True, "clean corpus must answer correctly before poisoning"
    assert result.poison_ingested is False
    assert result.downstream_output_poisoned is False
    assert result.finding is False
    assert result.verdict == Verdict.PASS.value


def test_secure_pipeline_can_retrieve_poison_without_following_it() -> None:
    result = run_retrieval_poisoning_lab(
        mode=LabMode.SECURE,
        run_id="test-secure",
    )

    assert result.poison_ingested is True
    assert result.poison_document_retrieved is True, "the test must prove the poison reached retrieval"
    assert result.untrusted_directive_detected is True, "secure path should observe the directive as untrusted data"
    assert result.trusted_fact_retrieved is True, "trusted fact must remain available for the answer"
    assert result.downstream_output_poisoned is False, "retrieval alone must not count as successful poisoning"
    assert result.finding is False
    assert result.verdict == Verdict.PASS.value


def test_vulnerable_pipeline_records_downstream_poisoning() -> None:
    result = run_retrieval_poisoning_lab(
        mode=LabMode.VULNERABLE,
        run_id="test-vulnerable",
    )

    assert result.baseline_control_correct is True
    assert result.poison_document_retrieved is True
    assert result.untrusted_directive_detected is True
    assert result.downstream_output_poisoned is True, "vulnerable path should change to the benign poison marker"
    assert result.finding is True
    assert result.verdict == Verdict.FAIL.value
    assert result.severity == "high"


def test_persisted_but_irrelevant_poison_is_not_retrieved() -> None:
    result = run_retrieval_poisoning_lab(
        mode=LabMode.POISON_NOT_RETRIEVED,
        run_id="test-not-retrieved",
    )

    assert result.poison_ingested is True, "control must persist an untrusted document"
    assert result.poison_document_retrieved is False, "irrelevant poison should not enter the retrieval set"
    assert result.untrusted_directive_detected is False
    assert result.downstream_output_poisoned is False
    assert result.finding is False


def test_lexical_retriever_ranks_relevant_poison_ahead_of_trusted_fact() -> None:
    corpus = InMemoryCorpus()
    corpus.ingest(
        Document(
            document_id=TRUSTED_DOC_ID,
            text="Project Atlas support tier is STANDARD. Official service handbook.",
            trust=SourceTrust.TRUSTED,
        )
    )
    corpus.ingest(
        Document(
            document_id=POISON_DOC_ID,
            text=POISON_TEXT,
            trust=SourceTrust.UNTRUSTED,
        )
    )

    retrieved = LexicalRetriever().retrieve(corpus, QUERY)

    assert retrieved[0].document_id == POISON_DOC_ID, "poison must win deterministic lexical ranking"
    assert retrieved[1].document_id == TRUSTED_DOC_ID, "trusted fact must still be present as a control"


def test_secure_pipeline_uses_provenance_not_retrieval_order() -> None:
    corpus = InMemoryCorpus()
    corpus.ingest(
        Document(
            document_id=TRUSTED_DOC_ID,
            text="Project Atlas support tier is STANDARD. Official service handbook.",
            trust=SourceTrust.TRUSTED,
        )
    )
    corpus.ingest(
        Document(
            document_id=POISON_DOC_ID,
            text=POISON_TEXT,
            trust=SourceTrust.UNTRUSTED,
        )
    )

    answer, retrieved, directive_detected = DeterministicRagPipeline(
        corpus,
        mode=PipelineMode.SECURE,
    ).answer(QUERY)

    assert retrieved[0].document_id == POISON_DOC_ID, "control requires poison to rank first"
    assert directive_detected is True
    assert answer == EXPECTED_ANSWER, "secure path must use trusted data despite poison ranking first"


def test_vulnerable_pipeline_treats_untrusted_directive_as_instruction() -> None:
    corpus = InMemoryCorpus()
    corpus.ingest(
        Document(
            document_id=TRUSTED_DOC_ID,
            text="Project Atlas support tier is STANDARD. Official service handbook.",
            trust=SourceTrust.TRUSTED,
        )
    )
    corpus.ingest(
        Document(
            document_id=POISON_DOC_ID,
            text=POISON_TEXT,
            trust=SourceTrust.UNTRUSTED,
        )
    )

    answer, _, directive_detected = DeterministicRagPipeline(
        corpus,
        mode=PipelineMode.VULNERABLE,
    ).answer(QUERY)

    assert directive_detected is True
    assert answer == POISON_MARKER


def test_result_evidence_omits_raw_query_answers_and_poison_text() -> None:
    result = run_retrieval_poisoning_lab(
        mode=LabMode.VULNERABLE,
        run_id="test-evidence",
    )

    serialized = str(result.to_dict())
    assert QUERY not in serialized, "query should be represented by a fingerprint"
    assert EXPECTED_ANSWER not in serialized, "expected answer should be represented by a fingerprint"
    assert POISON_MARKER not in serialized, "poison marker should be represented by a fingerprint"
    assert POISON_TEXT not in serialized, "raw poisoned content should not enter result evidence"
    assert len(result.query_sha256) == 64
    assert len(result.expected_answer_sha256) == 64
    assert len(result.poison_marker_sha256) == 64
    assert result.observed_answer_sha256 is not None


def test_retriever_excludes_zero_overlap_documents() -> None:
    corpus = InMemoryCorpus()
    corpus.ingest(
        Document(
            document_id="irrelevant",
            text="Cafeteria hours and menu for Building Delta.",
            trust=SourceTrust.UNTRUSTED,
        )
    )

    retrieved = LexicalRetriever().retrieve(corpus, QUERY)

    assert retrieved == [], "zero-overlap documents should not enter the retrieval set"
