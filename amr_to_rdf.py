#!/usr/bin/env python
"""
amr_to_rdf.py

Note, this is derived from the source code to AMRICA's disagree.py script by Naomi Saphra (nsaphra@jhu.edu)
Copyright(c) 2015. All rights reserved.

"""

import argparse
import argparse_config
import codecs
import os
import re

from compare_smatch import amr_metadata
from rdflib.namespace import RDF

cur_sent_id = 0
  
def run_main(args):
  try:
    import rdflib
  except ImportError:
    raise ImportError('requires rdflib')

  infile = codecs.open(args.infile, encoding='utf8')
  outfile = open(args.outfile, 'w')
  
  # create the basic RDF data structure
  g = rdflib.Graph()

  # namespaces
  amr_ns = rdflib.Namespace("http://amr.isi.edu/rdf/core-amr#")
  pb_ns = rdflib.Namespace("https://verbs.colorado.edu/propbank#")
  ontonotes_ns = rdflib.Namespace("https://catalog.ldc.upenn.edu/LDC2013T19#")
  amr_ne_ns = rdflib.Namespace("http://amr.isi.edu/entity-types#")
  up_ns = rdflib.Namespace("http://www.uniprot.org/uniprot/")
  pfam_ns = rdflib.Namespace("http://pfam.xfam.org/family/")
  
  ns_lookup = {}
  nelist = []
  nefile = codecs.open("ne.txt", encoding='utf8')
  for l in nefile:
    for w in re.split(",\s*", l):
        nelist.append( w )
  for ne in nelist:
      ns_lookup[ne] = amr_ne_ns  
  
  amrs_same_sent = []
  cur_id = ""
  while True:
    (amr_line, comments) = amr_metadata.get_amr_line(infile)
    cur_amr = None
    if amr_line:
      cur_amr = amr_metadata.AmrMeta.from_parse(amr_line, comments)
      if not cur_id:
        cur_id = cur_amr.metadata['id']

    if cur_amr is None or cur_id != cur_amr.metadata['id']:
      amr = amrs_same_sent[0]

      (inst, rel1, rel2) = amr.get_triples2()
    
      temp_ns = rdflib.Namespace("http://amr.isi.edu/amr_data/" + amr.metadata['id'] + "#")  
      a1 = temp_ns.root01 # reserve term root01 
      
      # :a1 rdf:type amr:AMR .
      g.add( (a1, rdflib.RDF.type, amr_ns.AMR) )

      #:a1 amr:has-sentence "Sos-1 has been shown to be part of a signaling complex with Grb2, which mediates the activation of Ras upon RTK stimulation." .
      g.add( (a1, amr_ns['has-sentence'], rdflib.Literal(amr.metadata['snt'])))

      #:a1 amr:has-id "pmid_1177_7939.53"
      g.add( (a1, amr_ns['has-id'], rdflib.Literal(amr.metadata['id'])))
      

      #:a1 amr:has-date "2015-03-07T10:57:15
      g.add( (a1, amr_ns['has-date'], rdflib.Literal(amr.metadata['date'])))

      #:a1 amr:has-annotator SDL-AMR-09
      #:a1 amr:is-preferred "true"^^xsd:boolean
      #:a1 amr:has-file "pmid_1177_7939_53.txt"
      
      g.add( (a1, amr_ns.root, temp_ns[amr.root]) )

      for (p, s, o) in inst:
        if( ns_lookup.get(o,None) is not None ):
            o_resolved = amr_ne_ns[o]
        elif( re.search('\-\d+$', o) is not None ):
            o_resolved = pb_ns[o]
        else: 
            o_resolved = amr_ns[o]
         
        g.add( (temp_ns[s], RDF.type, o_resolved) )

      for (p, s, o) in rel2:
        g.add( (temp_ns[s], amr_ns[p], temp_ns[o]) )

      for (p, s, l) in rel1:
        g.add( (temp_ns[s], amr_ns[p], rdflib.Literal(l) ) )
      
      amrs_same_sent = []
      if cur_amr is not None:
        cur_id = cur_amr.metadata['id']
      else:
        break

    amrs_same_sent.append(cur_amr)

  outfile.write( g.serialize(format=args.format) )
  outfile.close()

  infile.close()
  
  
 # gold_aligned_fh and gold_aligned_fh.close()

if __name__ == '__main__':
  parser = argparse.ArgumentParser()
  parser.add_argument('-i', '--infile', help='amr input file')
  parser.add_argument('-o', '--outfile', help='RDF output file')
  parser.add_argument('-v', '--verbose', action='store_true')
  parser.add_argument('-f', '--format', nargs='?', default='nt',
        help="RDF Format: xml, n3, nt, trix, rdfa")

  args = parser.parse_args()
  
  run_main(args)

