from __future__ import annotations
from xml.etree import ElementTree

from app.services.live_search import dailymed, pubchem, pubmed


def test_resolve_dailymed_workspace_extracts_label_signals(monkeypatch) -> None:
    xml_payload = """
    <document xmlns="urn:hl7-org:v3">
      <title>Aspirin tablet label</title>
      <code displayName="drug_label" />
      <effectiveTime value="20260508" />
      <setId root="dm-set-1" />
      <author>
        <assignedEntity>
          <representedOrganization>
            <name>Example Labs</name>
          </representedOrganization>
        </assignedEntity>
      </author>
      <component>
        <structuredBody>
          <component>
            <section>
              <title>Uses</title>
              <text><paragraph>Temporarily relieves minor aches and fever.</paragraph></text>
            </section>
          </component>
          <component>
            <section>
              <title>Directions</title>
              <text><paragraph>Take 1 to 2 tablets every 4 hours.</paragraph></text>
            </section>
          </component>
          <component>
            <section>
              <title>Warnings</title>
              <text><paragraph>Do not use if you have a bleeding disorder.</paragraph></text>
            </section>
          </component>
        </structuredBody>
      </component>
      <manufacturedProduct>
        <name>Aspirin</name>
      </manufacturedProduct>
      <asEntityWithGeneric>
        <genericMedicine>
          <name>aspirin</name>
        </genericMedicine>
      </asEntityWithGeneric>
      <routeCode displayName="ORAL" />
      <ingredient>
        <ingredientSubstance>
          <name>aspirin</name>
        </ingredientSubstance>
      </ingredient>
    </document>
    """

    monkeypatch.setattr(
        dailymed,
        "_fetch_xml",
        lambda *_args, **_kwargs: ElementTree.fromstring(xml_payload),
    )

    workspace = dailymed.resolve_dailymed_workspace(
        entity_type="molecule",
        external_id="dm-set-1",
        query="aspirin",
    )

    assert [signal.key for signal in workspace.extracted_signals] == [
        "route",
        "active_ingredients",
        "use_case",
        "dosage_guidance",
        "warning_signal",
        "manufacturer",
    ]
    assert workspace.pod_analysis.primary_candidate is None


def test_resolve_pubmed_workspace_extracts_literature_signals(monkeypatch) -> None:
    monkeypatch.setattr(
        pubmed,
        "_fetch_pubmed_summary_records",
        lambda _ids: [
            {
                "uid": "12345",
                "title": "A clinical aspirin exposure study",
                "fulljournalname": "Journal of Safety",
                "pubdate": "2025 May",
                "authors": [{"name": "Smith J"}],
            }
        ],
    )

    xml_payload = """
    <PubmedArticleSet>
      <PubmedArticle>
        <MedlineCitation>
          <Article>
            <ArticleTitle>A clinical aspirin exposure study</ArticleTitle>
            <Journal><Title>Journal of Safety</Title></Journal>
            <Abstract>
              <AbstractText>Healthy volunteers received oral aspirin 50 mg/kg/day and plasma exposure was monitored.</AbstractText>
              <AbstractText>NOAEL was identified at 50 mg/kg/day in the supporting toxicology package.</AbstractText>
            </Abstract>
            <PublicationTypeList>
              <PublicationType>Clinical Trial</PublicationType>
            </PublicationTypeList>
            <AuthorList>
              <Author><LastName>Smith</LastName><Initials>J</Initials></Author>
            </AuthorList>
          </Article>
          <KeywordList>
            <Keyword>aspirin</Keyword>
            <Keyword>exposure</Keyword>
          </KeywordList>
        </MedlineCitation>
      </PubmedArticle>
    </PubmedArticleSet>
    """

    monkeypatch.setattr(
        pubmed,
        "_fetch_xml",
        lambda *_args, **_kwargs: ElementTree.fromstring(xml_payload),
    )

    workspace = pubmed.resolve_pubmed_workspace(
        entity_type="molecule",
        external_id="12345",
        query="aspirin",
    )

    signal_keys = [signal.key for signal in workspace.extracted_signals]
    assert "evidence_focus" in signal_keys
    assert "study_model" in signal_keys
    assert "route_mentions" in signal_keys
    assert "dose_or_exposure_context" in signal_keys
    assert "dose_sentence" in signal_keys
    assert "pod_signal" in signal_keys
    assert "pod_candidate" in signal_keys
    assert "exposure_signal" in signal_keys
    assert "toxicology_takeaway" in signal_keys
    assert "publication_type" in signal_keys
    assert workspace.pod_analysis.primary_candidate is not None
    assert workspace.pod_analysis.primary_candidate.pod_term == "NOAEL"
    assert workspace.pod_analysis.derived_calculations[0].label == "50 kg screening conversion"


def test_resolve_pubchem_workspace_extracts_identity_and_hazard_signals(monkeypatch) -> None:
    def fake_fetch_json(url: str):
        if "property" in url:
            return {
                "PropertyTable": {
                    "Properties": [
                        {
                            "CID": 2244,
                            "Title": "Aspirin",
                            "MolecularFormula": "C9H8O4",
                            "MolecularWeight": "180.16",
                            "ConnectivitySMILES": "CC(=O)OC1=CC=CC=C1C(=O)O",
                            "InChIKey": "BSYNRYMUTXBXSQ-UHFFFAOYSA-N",
                            "IUPACName": "2-acetyloxybenzoic acid",
                            "XLogP": 1.2,
                            "TPSA": 63.6,
                        }
                    ]
                }
            }
        if "synonyms" in url:
            return {
                "InformationList": {
                    "Information": [
                        {"CID": 2244, "Synonym": ["aspirin", "ACETYLSALICYLIC ACID", "Ecotrin"]}
                    ]
                }
            }
        return {
            "Record": {
                "Section": [
                    {
                        "TOCHeading": "Toxicity",
                        "Section": [
                            {
                                "TOCHeading": "Toxicity Summary",
                                "Information": [
                                    {
                                        "Value": {
                                            "StringWithMarkup": [
                                                {"String": "Overdose can cause salicylate toxicity."}
                                            ]
                                        }
                                    }
                                ],
                            }
                        ],
                    }
                ]
            }
        }

    monkeypatch.setattr(pubchem, "_fetch_json", fake_fetch_json)

    workspace = pubchem.resolve_pubchem_workspace(
        entity_type="molecule",
        external_id="2244",
        query="aspirin",
    )

    signal_keys = [signal.key for signal in workspace.extracted_signals]
    assert workspace.record.provider == "pubchem"
    assert "molecular_formula" in signal_keys
    assert "toxicity_signal" in signal_keys
    assert workspace.sections[0].title == "Chemical profile"
