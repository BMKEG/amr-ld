#!/usr/bin/env python
"""
amr_to_jsonld.py

Note, this is derived from the source code to AMRICA's disagree_btwn_sents.py script by Naomi Saphra (nsaphra@jhu.edu)
Copyright(c) 2015. All rights reserved.

"""

import argparse
import argparse_config
import codecs
import os
import re
import json

from compare_smatch import amr_metadata

cur_sent_id = 0
  
def run_main(args):
  try:
    import rdflib
  except ImportError:
    raise ImportError('requires rdflib')

  infile = codecs.open(args.infile, encoding='utf8')
  outfile = open(args.outfile, 'w')
  
  json_obj = []
  
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

      # lookup from original amr objects and simple python objects
      lookup = {}
      context = {}
    

      default = "http://amr.isi.edu/amr_data/" + amr.metadata['id'] + "#" 
      temp_ns = rdflib.Namespace(default)  

      a1 = {}
      a1["@type"] = amr_ns.AMR.toPython()
      json_obj.append(a1)

      #:a1 amr:has-sentence "Sos-1 has been shown to be part of a signaling complex with Grb2, which mediates the activation of Ras upon RTK stimulation." .
      a1['has-sentence'] = amr.metadata['snt']

      #:a1 amr:has-id "pmid_1177_7939.53"
      a1['@id'] = amr.metadata['id']
      
      #:a1 amr:has-date "2015-03-07T10:57:15
      a1['has-date'] = amr.metadata['date']

      #:a1 amr:has-annotator SDL-AMR-09
      #:a1 amr:is-preferred "true"^^xsd:boolean
      #:a1 amr:has-file "pmid_1177_7939_53.txt"
      
      amr_root = {}
      lookup[amr.root] = amr_root 
      a1['root'] = amr_root
      context['root'] = amr_ns.root.toPython()
      context['@base'] = default

      for (p, s, o) in inst:
        
        if( ns_lookup.get(o,None) is not None ):
            context[o] = amr_ne_ns[o].toPython()
        elif( re.search('\-\d+$', o) is not None ):
            context[o] = pb_ns[o].toPython()        
        else: 
            context[o] = amr_ns[o].toPython()
            
        if( lookup.get(s,None) is None ):
           lookup[s] = {}
        
        s_obj = lookup[s]
        s_obj["@id"] = s
        s_obj["@type"] = o
                
      for (p, s, o) in rel2:
          
        if( lookup.get(s,None) is None ):
           lookup[s] = {}

        if( lookup.get(o,None) is None ):
           lookup[o] = {}

        s_obj = lookup[s]
        o_obj = lookup[o]

        if( s != o ):
            s_obj[p] = o_obj
        
      for (p, s, l) in rel1:
          
        if( lookup.get(s,None) is None ):
           lookup[s] = {}

        s_obj = lookup[s]
        o_obj = lookup[o]

        s_obj[p] = l
        
      a1['@context'] = context 
      
      amrs_same_sent = []
      if cur_amr is not None:
        cur_id = cur_amr.metadata['id']
      else:
        break

    amrs_same_sent.append(cur_amr)

  json.dump( json_obj, outfile, indent=2 )
  outfile.close()

  infile.close()
  
 # gold_aligned_fh and gold_aligned_fh.close()

if __name__ == '__main__':
  parser = argparse.ArgumentParser()
  parser.add_argument('-i', '--infile', help='amr input file')
  parser.add_argument('-o', '--outfile', help='RDF output file')

  args = parser.parse_args()
  
  run_main(args)

