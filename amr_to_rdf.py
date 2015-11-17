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
from rdflib.namespace import RDFS
from rdflib.plugins import sparql
from Carbon.QuickDraw import frame

cur_sent_id = 0
    
def strip_word_alignments(str, patt):    
    match = patt.match(str)
    if match:
        str = match.group(1)
        
    return str
            
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

    # Basic AMR Ontology consisting of 
    #   1. concepts
    #   2. roles 
    #   3. strings (which are actually going to be Literal(string)s
    conceptClass = amr_ns.Concept
    neClass = amr_ns.NamedEntity
    frameClass = amr_ns.Frame
    roleClass = amr_ns.Role
    frameRoleClass = pb_ns.FrameRole
    
    g.add( (conceptClass, rdflib.RDF.type, rdflib.RDFS.Class) )
    g.add( (conceptClass, RDFS.label, rdflib.Literal("AMR_Concept") ) )
    g.add( (conceptClass, RDFS.comment, rdflib.Literal("Class of all concepts expressed in AMRs") ) )

    g.add( (neClass, rdflib.RDF.type, conceptClass) )
    g.add( (neClass, RDFS.label, rdflib.Literal("AMR_NamedEntity") ) )
    g.add( (neClass, RDFS.comment, rdflib.Literal("Class of all named entities expressed in AMRs") ) )

    g.add( (frameClass, rdflib.RDF.type, conceptClass) )
    g.add( (frameClass, RDFS.label, rdflib.Literal("AMR_Frame") ) )
    g.add( (frameClass, RDFS.comment, rdflib.Literal("Class of all frames expressed in AMRs") ) )

    g.add( (roleClass, rdflib.RDF.type, rdflib.RDFS.Class) )
    g.add( (roleClass, RDFS.label, rdflib.Literal("AMR_Role") ) )
    g.add( (roleClass, RDFS.comment, rdflib.Literal("Class of all roles expressed in AMRs") ) )

    g.add( (frameRoleClass, rdflib.RDF.type, roleClass) )
    g.add( (frameRoleClass, RDFS.label, rdflib.Literal("FrameRole") ) )
    g.add( (frameRoleClass, RDFS.comment, rdflib.Literal("Class of all roles of PropBank frames") ) )
    
    amr_count = 0
    ns_lookup = {}
    nelist = []
    pmid_patt = re.compile('.*pmid_(\d+)_(\d+).*')
    word_align_patt = re.compile('(.*)\~e\.(.+)')
    opN_patt = re.compile('op(\d+)')
    arg_patt = re.compile('ARG\d+')

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
        label_lookup_table = {}
    
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
            g.add( (a1, 
                    rdflib.RDF.type, 
                    amr_ns.AMR) )

            #:a1 amr:has-id "pmid_1177_7939.53"
            amr_id = amr.metadata['id']
            g.add( (a1, 
                    amr_ns['has-id'], 
                    rdflib.Literal(amr_id)))
            
            match = pmid_patt.match(amr_id)
            if match:
                    pmid = match.group(1) + match.group(2)
                    g.add( (a1, 
                            amr_ns['has-pmid'], 
                            rdflib.Literal(pmid)))

            #:a1 amr:has-sentence "Sos-1 has been shown to be part of a signaling complex with Grb2, which mediates the activation of Ras upon RTK stimulation." .
            if( amr.metadata.get('snt', None) is not None):
                    g.add( (a1, 
                            amr_ns['has-sentence'], 
                            rdflib.Literal(amr.metadata['snt'])))

            #:a1 amr:has-date "2015-03-07T10:57:15
            if( amr.metadata.get('date', None) is not None):
                    g.add( (a1, 
                            amr_ns['has-date'], 
                            rdflib.Literal(amr.metadata['date'])))

            #:a1 amr:amr-annotator SDL-AMR-09
            if( amr.metadata.get('amr-annotator', None) is not None):
                    g.add( (a1,
                            amr_ns['has-annotator'], 
                            rdflib.Literal(amr.metadata['amr-annotator'])))
                    
            #:a1 amr:tok 
            if( amr.metadata.get('tok', None) is not None):
                    g.add( (a1, 
                            amr_ns['has-tokens'], 
                            rdflib.Literal(amr.metadata['tok'])))

            #:a1 amr:alignments
            if( amr.metadata.get('alignments', None) is not None):
                    g.add( (a1, 
                            amr_ns['has-alignments'], 
                            rdflib.Literal(amr.metadata['alignments'])))
            
            g.add( (a1, amr_ns.root, temp_ns[amr.root]) )

            # Add triples for setting types pointing to other resources
            frames = {}
            for (p, s, o) in inst:
                    
                o = strip_word_alignments(o,word_align_patt)
                #if word_pos is not None:
                #        g.add( (temp_ns[s], 
                #                        amr_ns['has-word-pos'], 
                #                        rdflib.Literal(word_pos)) )            
                  
                if( ns_lookup.get(o,None) is not None ):
                    o_resolved = amr_ne_ns[o]
                    g.add( (o_resolved, rdflib.RDF.type, neClass) )
                elif( re.search('\-\d+$', o) is not None ):
                    o_resolved = pb_ns[o]
                    g.add( (o_resolved, rdflib.RDF.type, frameClass) ) 
                elif( o != 'name' ): # ignore 'name' objects but add all others
                    o_resolved = amr_ns[o]
                    g.add( (o_resolved, rdflib.RDF.type, conceptClass) )
                 
                frames[s] = o
                g.add( (temp_ns[s], RDF.type, o_resolved) )

            # Add object properties for local links in the current AMR
            for (p, s, o) in rel2:
                
                if( p == "TOP" ):
                    continue
                 
                # Do not include word positions for predicates 
                # (since they are more general and do not need to linked to everything).     
                p = strip_word_alignments(p,word_align_patt)                
                o = strip_word_alignments(o,word_align_patt)
                                
                # remember which objects have name objects 
                if( p == 'name' ):
                    label_lookup_table[o] = s 
                elif( re.search('ARG\d+$', p) is not None ):
                    frameRole = frames[s] + "." + p
                    g.add( (pb_ns[frameRole], rdflib.RDF.type, frameRoleClass) )
                    g.add( (temp_ns[s], pb_ns[frameRole], temp_ns[o] ) )                    
                else:
                    g.add( (amr_ns[p], rdflib.RDF.type, roleClass) )
                    g.add( (temp_ns[s], amr_ns[p], temp_ns[o]) )

            # Add data properties in the current AMR
            labels = {}
            for (p, s, l) in rel1:

                p = strip_word_alignments(p, word_align_patt)
                l = strip_word_alignments(l, word_align_patt)
                
                #
                # Build labels across multiple 'op1, op2, ... opN' links, 
                #
                opN_match = re.match(opN_patt, p)
                if( opN_match is not None and
                        label_lookup_table.get(s,None) is not None):
                    opN = int(opN_match.group(1))
                    ss = label_lookup_table[s]
                    if( labels.get(ss, None) is None ):
                        labels[ss] = []
                    
                    labels[ss].append( (opN, l) )

                # Special treatment for propbank roles.                 
                elif( re.search('ARG\d+$', p) is not None ):
                    frameRole = frames[s] + "." + p
                    g.add( (pb_ns[frameRole], rdflib.RDF.type, frameRoleClass) )
                    g.add( (temp_ns[s], pb_ns[frameRole], rdflib.Literal(l) ) )                    
                
                # Otherwise, it's just a literal 
                else:
                    g.add( (temp_ns[s], amr_ns[p], rdflib.Literal(l) ) )
            
            # Add labels here
            # ["\n".join([i.split(' ')[j] for j in range(5)]) for i in g.vs["id"]]
            for key in labels.keys():
                labelArray = [i[1] for i in sorted(labels[key])];
                
                label = " ".join( labelArray )
                g.add( (temp_ns[key], 
                        RDFS.label, 
                        rdflib.Literal(label) ) )
            
            amrs_same_sent = []
            if cur_amr is not None:
                cur_id = cur_amr.metadata['id']
            else:
                break

        amrs_same_sent.append(cur_amr)
        amr_count = amr_count+1

    # Additional processing to clean up. 
    # 1. Add labels to AMR objects
    #q = sparql.prepareQuery("select distinct ?s ?label " +
    #                                                "where { " +
    #                                                "?s <http://amr.isi.edu/rdf/core-amr#name> ?n . " +
    #                                                "?n <http://amr.isi.edu/rdf/core-amr#op1> ?label " +
    #                                                "}")
    #qres = g.query(q)

    #for row in qres:
    #    print("%s type %s" % row)
    print ("%d AMRs converted" % amr_count)
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

