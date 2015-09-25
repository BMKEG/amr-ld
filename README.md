# AMR-LD (AMRs as Linked Data)

## Advantages of AMR-LD

- Sharable in standard W3C format

- Some reasoning for free (using RDF/OWL tools):
  - amr:ARG0-of owl:inverseOf amr:ARG0
  - inheritance reasoning:
  
  ```
    If :p rdf:type amr-ne:enzyme .
       ame-ne:enzyme rdfs:subClassOf amr-ne:protein .
    Then :p rdf:type amr-ne:protein
  ```

- Linked to well know identifiers/entities

  ```
    :e amr:xref up:RASH_HUMAN .
    :e amr:xref pfam:PF00071 .
  ```

- Making semantic assertions of precise equivalence using `owl:sameAs` relations

  ```
    :e owl:sameAs up:RASH_HUMAN .
  ```

- Query tools for free (SPARQL)
  - Names of proteins in a AMR repository

  ```
    select ?n
    where  { ?p rdf:type amr-ne:protein .
         ?p amr:name ?no .
       ?no rdf:type amr-ne:name .
       ?no :op1 ?n }
  ```

   - All propbank events (verbs) that have a protein as :ARG1

  ```
    select ?v
    where { ?e rdf:type ?v .
          ?e amr:ARG1 ?p .
       ?p rdf:type amr-ne:protein .
       ### we would get all the "amr-ne:enzyme"s if reasoning enabled
       }
  ```

   - All propbank events (verbs) that have a protein as :ARG*

  ```
    select ?v
    where { ?e rdf:type ?v .
          ?e ?arg ?p .
       ?p rdf:type amr-ne:protein .
       ### we would get all the "amr-ne:enzyme"s if reasoning enabled
       FILTER regex(?arg, "ARG", "i") }
       }
  ```
## 2. AMR-LD example

The cjconsensus Gold-Standard data set contains the following AMR (from a sentence in the results section of [Innocenti et al. 2002](http://www.ncbi.nlm.nih.gov/pubmed/11777939)):

```
# ::id pmid_1177_7939.53 ::date 2015-03-07T10:57:15 ::annotator SDL-AMR-09 ::preferred
# ::snt Sos-1 has been shown to be part of a signaling complex with Grb2, which mediates the activation of Ras upon RTK stimulation.
# ::save-date Fri Mar 13, 2015 ::file pmid_1177_7939_53.txt
(s / show-01
      :ARG1 (h / have-part-91
            :ARG1 (m / macro-molecular-complex
                  :ARG0-of (s2 / signal-07)
                  :part (p2 / protein :name (n2 / name :op1 "Grb2")
                        :ARG0-of (m2 / mediate-01
                              :ARG1 (a / activate-01
                                    :ARG1 (e / enzyme :name (n3 / name :op1 "Ras"))
                                    :condition (s3 / stimulate-01
                                          :ARG1 (e2 / enzyme :name (n4 / name :op1 "RTK")))))))
            :ARG2 (p / protein :name (n / name :op1 "Sos-1"))))
```

Under our current rubric, this would then be translated to the following RDF TTL code, with a fairly simple one-to-one mapping from AMR elements to RDF elements.  

```
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>.
@prefix xsd: <http://www.w3.org/2001/XMLSchema#>.

@prefix amr: <http://amr.isi.edu#>
@prefix pb: <https://verbs.colorado.edu/propbank#>
@prefix ontonotes: <https://catalog.ldc.upenn.edu/LDC2013T19#>
@prefix amr-ne: <http://amr.isi.edu/entity-types#>

@prefix up: <http://www.uniprot.org/uniprot/>
@prefix pfam: <http://pfam.xfam.org/family/>


### : is the default namespace

:a1 rdf:type amr:AMR .
:a1 amr:has-sentence "Sos-1 has been shown to be part of a signaling complex with Grb2, which mediates the activation of Ras upon RTK stimulation." .
:a1 amr:has-id "pmid_1177_7939.53"
:a1 amr:has-date "2015-03-07T10:57:15
:a1 amr:has-annotator SDL-AMR-09
:a1 amr:is-preferred "true"^^xsd:boolean
:a1 amr:has-file "pmid_1177_7939_53.txt"

:a1 amr:has-root :s .   ### or :a1 amr:has-root :pmid_1177_7939.53__s
:s rdf:type pb:show-01 .
:s amr:ARG1 :h .
:h rdf:type pb:have-part-91 .
:h amr:ARG1 :m .
:m rdf:type amr-ne:macro-molecular-complex .
:m amr:ARG0-of :s2 .
:s2 rdf:type pb:signal-07 .
:m amr:part :p2 .
:p2 rdf:type amr-ne:protein .
:p2 :name :n2 .
:n2 rdf:type amr-ne:name .
:n2 amr:op1 "Grb2" .
:p2 amr:xref up:P62993 .
:p2 amr:xref up:GRB2_HUMAN .
:p2 amr:ARG0-of :m2 .
:m2 rdf:type pb:mediate-01 .
:m2 amr:ARG1 :a .
:a rdf:type pb:activate-01 .
:a amr:ARG1 :e .
:e rdf:type amr-ne:enzyme .
:e :name :n3 .
:n3 rdf:type amr-ne:name .
:n3 :op1 "Ras" .
:e amr:xref up:RASH_HUMAN .     ### we could also do:   :e owl:sameAs up:RASH_HUMAN  
:e amr:xref pfam:PF00071 .
:a amr:condition :s3 .
:s3 rdf:type pb:stimulate-01 .
:s3 amr:ARG1 :e2 .
:e2 rdf:type amr-ne:enzyme .
:e2 amr:name :n4 .
:n4 rdf:type amr-ne:name .
:n4 :op1 "RTK" .
:e2 amr:xref pfam:PF07714
:h amr:ARG2 :p .
:p rdf:type amr-ne:protein .
:p amr:name :n .
:n rdf:type amr:name .
:n :op1 "Sos-1" .
```
