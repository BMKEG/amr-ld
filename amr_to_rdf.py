#!/usr/bin/env python
"""
amr_to_rdf.py

Note, this is derived from the source code to AMRICA's disagree_btwn_sents.py script by Naomi Saphra (nsaphra@jhu.edu)
Copyright(c) 2015. All rights reserved.

"""

import argparse
import argparse_config
import codecs
import os
import re
import textwrap

from compare_smatch import amr_metadata
from rdflib.namespace import RDF
from rdflib.namespace import RDFS
from rdflib.plugins import sparql
from Carbon.QuickDraw import frame
from numpy.f2py.auxfuncs import throw_error

cur_sent_id = 0
    
def strip_word_alignments(str, patt):    
    match = patt.match(str)
    if match:
        str = match.group(1)
        
    return str
            
def run_main(args): 

    inPath = args.inPath
    outPath = args.outPath

    #
    # If the path is a directory then loop over the directory contents,
    # Else run the script on the file as described
    #
    if( os.path.isfile(inPath) ):
        run_main_on_file(args)
    else:
        if not os.path.exists(outPath):
            os.makedirs(outPath)
        for fn in os.listdir(inPath):
            if os.path.isfile(inPath+"/"+fn) and fn.endswith(".txt"):
                args.inPath =inPath + "/" + fn
                args.outPath = outPath + "/" + fn + ".rdf"
                run_main_on_file(args)

def run_main_on_file(args):
    
    try:
        import rdflib
    except ImportError:
        raise ImportError('requires rdflib')
                
    infile = codecs.open(args.inPath, encoding='utf8')
    outfile = open(args.outPath, 'w')
    
    pBankRoles = True
    if( not(args.pbankRoles == u'1') ):
        pBankRoles = False
                                
    xref_namespace_lookup = {}
    with open('xref_namespaces.txt') as f:
        xref_lines = f.readlines()
    for l in xref_lines:
        line = re.split("\t", l)
        xref_namespace_lookup[line[0]] = line[1].rstrip('\r\n')
                                
    # create the basic RDF data structure
    g = rdflib.Graph()
    
    # namespaces
    amr_ns = rdflib.Namespace("http://amr.isi.edu/rdf/core-amr#")
    amr_terms_ns = rdflib.Namespace("http://amr.isi.edu/rdf/amr-terms#")
    amr_data = rdflib.Namespace("http://amr.isi.edu/amr_data#")
    pb_ns = rdflib.Namespace("http://amr.isi.edu/frames/ld/v1.2.2/")
    amr_ne_ns = rdflib.Namespace("http://amr.isi.edu/entity-types#")

    up_ns = rdflib.Namespace("http://www.uniprot.org/uniprot/")
    pfam_ns = rdflib.Namespace("http://pfam.xfam.org/family/")
    ontonotes_ns = rdflib.Namespace("https://catalog.ldc.upenn.edu/LDC2013T19#")

    g.namespace_manager.bind('propbank', pb_ns, replace=True)
    g.namespace_manager.bind('amr-core', amr_ns, replace=True)
    g.namespace_manager.bind('amr-terms', amr_terms_ns, replace=True)
    g.namespace_manager.bind('entity-types', amr_ne_ns, replace=True)    
    g.namespace_manager.bind('amr-data', amr_data, replace=True)    
    
    for k in xref_namespace_lookup.keys():
        temp_ns = rdflib.Namespace(xref_namespace_lookup[k])
        g.namespace_manager.bind(k, temp_ns, replace=True)    
        xref_namespace_lookup[k] = temp_ns
    
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
    g.add( (conceptClass, RDFS.label, rdflib.Literal("AMR-Concept") ) )
    #g.add( (conceptClass, RDFS.comment, rdflib.Literal("Class of all concepts expressed in AMRs") ) )

    g.add( (neClass, rdflib.RDF.type, conceptClass) )
    g.add( (neClass, RDFS.label, rdflib.Literal("AMR-EntityType") ) )
    #g.add( (neClass, RDFS.comment, rdflib.Literal("Class of all named entities expressed in AMRs") ) )

    g.add( (neClass, rdflib.RDF.type, conceptClass) )
    g.add( (neClass, RDFS.label, rdflib.Literal("AMR-Term") ) )
    #g.add( (neClass, RDFS.comment, rdflib.Literal("Class of all named entities expressed in AMRs") ) )

    g.add( (roleClass, rdflib.RDF.type, rdflib.RDFS.Class) )
    g.add( (roleClass, RDFS.label, rdflib.Literal("AMR-Role") ) )
    #g.add( (roleClass, RDFS.comment, rdflib.Literal("Class of all roles expressed in AMRs") ) )

    g.add( (frameRoleClass, rdflib.RDF.type, roleClass) )
    g.add( (frameRoleClass, RDFS.label, rdflib.Literal("AMR-PropBank-Role") ) )
    #g.add( (frameRoleClass, RDFS.comment, rdflib.Literal("Class of all roles of PropBank frames") ) )

    g.add( (frameClass, rdflib.RDF.type, conceptClass) )
    g.add( (frameClass, RDFS.label, rdflib.Literal("AMR-PropBank-Frame") ) )
    #g.add( (frameClass, RDFS.comment, rdflib.Literal("Class of all frames expressed in AMRs") ) )
    
    amr_count = 0
    ns_lookup = {}
    class_lookup = {}
    nelist = []
    corelist = []
    pattlist = []
    pmid_patt = re.compile('.*pmid_(\d+)_(\d+).*')
    word_align_patt = re.compile('(.*)\~e\.(.+)')
    propbank_patt = re.compile('^(.*)\-\d+$')
    opN_patt = re.compile('op(\d+)')
    arg_patt = re.compile('ARG\d+')

    with open('amr-ne.txt') as f:
        ne_lines = f.readlines()
    for l in ne_lines:
        for w in re.split(",\s*", l):
            w = w.rstrip('\r\n')
            nelist.append( w )
    for ne in nelist:
            ns_lookup[ne] = amr_ne_ns
            class_lookup[ne] = neClass

    with open('amr-core.txt') as f:
        core_lines = f.readlines()
    for l in core_lines:
        for w in re.split(",\s*", l):
            w = w.rstrip('\r\n')
            corelist.append( w )
    for c in corelist:
            ns_lookup[c] = amr_ns    
            class_lookup[c] = conceptClass
            
    pattfile = codecs.open("amr-core-patterns.txt", encoding='utf8')
    for l in pattfile:
        pattlist.append( w )
    
    amrs_same_sent = []
    
    cur_id = ""
    while True:
        (amr_line, comments) = amr_metadata.get_amr_line(infile)
        cur_amr = None

        vb_lookup = {}
        label_lookup_table = {}
        xref_variables = {}
    
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
                            rdflib.Literal(amr.metadata['snt']) )
                          )

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
                    resolved_ns = ns_lookup.get(o,None)
                    o_resolved = resolved_ns[o]
                    if( class_lookup.get(o,None) is not None): 
                        g.add( (o_resolved, rdflib.RDF.type, class_lookup.get(o,None)) )
                    else:
                        raise ValueError(o_resolved + ' does not have a class assigned.')
                elif( re.search('\-\d+$', o) is not None ):
                    #match = propbank_patt.match(o)
                    #str = ""
                    #if match:
                    #    str = match.group(1)
                    #o_resolved = pb_ns[str + ".html#" +o ]
                    o_resolved = pb_ns[ o ]
                    g.add( (o_resolved, rdflib.RDF.type, frameClass) ) 
                elif( o == 'xref' and args.fixXref): 
                    continue
                elif( not(o == 'name') ): # ignore 'name' objects but add all others.
                    o_resolved = amr_terms_ns[o]
                    g.add( (o_resolved, rdflib.RDF.type, conceptClass) )
                # identify xref variables in AMR, don't retain it as a part of the graph.
                else: 
                    continue
                 
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
                    
                # objects with value objects should also be in  
                elif( p == 'xref' and args.fixXref):
                    xref_variables[o] = s   
               
                elif( re.search('^ARG\d+$', p) is not None ):

                    frameRole = frames[s] + "." + p
                    if( not(pBankRoles) ): 
                        frameRole = p

                    g.add( (pb_ns[frameRole], rdflib.RDF.type, frameRoleClass) )
                    g.add( (temp_ns[s], pb_ns[frameRole], temp_ns[o] ) )                    
                    vb_lookup[s] = temp_ns[s]
                    vb_lookup[frameRole] = pb_ns[frameRole]
                    vb_lookup[o] = temp_ns[o]

                elif( re.search('^ARG\d+\-of$', p) is not None ):
                    
                    frameRole = frames[o] + "." + p
                    if( not(pBankRoles) ): 
                        frameRole = p
                        
                    g.add( (pb_ns[frameRole], rdflib.RDF.type, frameRoleClass) )
                    g.add( (temp_ns[s], pb_ns[frameRole], temp_ns[o] ) )        
                    vb_lookup[s] = temp_ns[s]
                    vb_lookup[frameRole] = pb_ns[frameRole]
                    vb_lookup[o] = temp_ns[o]
                
                else:
                
                    g.add( (amr_terms_ns[p], rdflib.RDF.type, roleClass) )
                    g.add( (temp_ns[s], amr_terms_ns[p], temp_ns[o]) )
                    vb_lookup[s] = temp_ns[s]
                    vb_lookup[p] = amr_terms_ns[p]
                    vb_lookup[o] = temp_ns[o]
    

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

                elif( xref_variables.get(s,None) is not None 
                      and p == 'value'
                      and args.fixXref):
                    for k in xref_namespace_lookup.keys():
                        if( l.startswith(k) ):
                            l2 = l[-len(l)+len(k):]
                            xref_vb = xref_variables.get(s,None)
                            resolved_xref_vb = vb_lookup.get(xref_vb,None)
                            g.add( (resolved_xref_vb, 
                                    amr_ns['xref'], 
                                    xref_namespace_lookup[k][l2]) )
                            
                # Special treatment for propbank roles.                 
                elif( re.search('ARG\d+$', p) is not None ):
                    
                    frameRole = frames[s] + "." + p
                    if( not(pBankRoles) ): 
                        frameRole = p
                    
                    g.add( (pb_ns[frameRole], rdflib.RDF.type, frameRoleClass) )
                    g.add( (temp_ns[s], pb_ns[frameRole], rdflib.Literal(l) ) )                    
                
                # Otherwise, it's just a literal 
                else:
                    g.add( (temp_ns[s], amr_terms_ns[p], rdflib.Literal(l) ) )
            
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
    
    parser.add_argument('-i', '--inPath', help='AMR input file or directory')
    parser.add_argument('-o', '--outPath', help='RDF output file or directory')

    parser.add_argument('-pbr', '--pbankRoles', default='1', help='Do we include PropBank Roles?')
    parser.add_argument('-kx', '--fixXref', default='1', help='Keep existing Xref formalism?')
    parser.add_argument('-v', '--verbose', action='store_true')
    parser.add_argument('-f', '--format', nargs='?', default='nt',
                        help="RDF Format: xml, n3, nt, trix, rdfa")

    args = parser.parse_args()
    
    run_main(args)

