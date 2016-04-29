#!/usr/bin/env python

"""
smatch-table.py

This file is from the code for smatch, available at:

http://amr.isi.edu/download/smatch-v1.0.tar.gz
http://amr.isi.edu/smatch-13.pdf
"""

import sys
import subprocess
from smatch import amr
from smatch import smatch
import os
import random
import time

from compare_smatch import amr_metadata
#import optparse
# import argparse #argparse only works for python 2.7. If you are using older versin of Python, you can use optparse instead.
#import locale

verbose = False  # global variable, verbose output control

single_score = True  # global variable, single score output control

pr_flag = False  # global variable, output precision and recall

ERROR_LOG = sys.stderr

match_num_dict = {}  # key: match number tuples    value: the matching number

isi_dir_pre = "/nfs/web/isi.edu/cgi-bin/div3/mt/save-amr"

def build_arg_parser():
  """Build an argument parser using argparse"""
  parser = argparse.ArgumentParser(
      description="Smatch calculator -- arguments")
  parser.add_argument(
      '-f',
      nargs=2,
      required=True,
      type=argparse.FileType('r'),
      help='Two files containing AMR pairs. AMRs in each file are separated by a single blank line')
  parser.add_argument(
      '-o',
      '--outfile',
      help='Output')
  parser.add_argument(
      '-r',
      type=int,
      default=4,
      help='Restart number (Default:4)')
  parser.add_argument(
      '-v',
      action='store_true',
      help='Verbose output (Default:False)')
  parser.add_argument(
      '--ms',
      action='store_true',
      default=False,
      help='Output multiple scores (one AMR pair a score) instead of a single document-level smatch score (Default: False)')
  parser.add_argument(
      '--pr',
      action='store_true',
      default=False,
      help="Output precision and recall as well as the f-score. Default: false")
  return parser

def build_arg_parser2():
  """Build an argument parser using optparse"""
  usage_str = "Smatch calculator -- arguments"
  parser = optparse.OptionParser(usage=usage_str)
  #parser.add_option("-h","--help",action="help",help="Smatch calculator -- arguments")
  parser.add_option(
      "-f",
      "--files",
      nargs=2,
      dest="f",
      type="string",
      help='Two files containing AMR pairs. AMRs in each file are separated by a single blank line. This option is required.')
  parser.add_option(
      "-o",
      "--outfile",
      nargs=1,
      dest="o",
      type="string",
      help='Output file.')
  parser.add_option(
      "-r",
      "--restart",
      dest="r",
      type="int",
      help='Restart number (Default: 4)')
  parser.add_option(
      "-v",
      "--verbose",
      action='store_true',
      dest="v",
      help='Verbose output (Default:False)')
  parser.add_option(
      "--ms",
      "--multiple_score",
      action='store_true',
      dest="ms",
      help='Output multiple scores (one AMR pair a score) instead of a single document-level smatch score (Default: False)')
  parser.add_option(
      '--pr',
      "--precision_recall",
      action='store_true',
      dest="pr",
      help="Output precision and recall as well as the f-score. Default: false")
  parser.set_defaults(r=4, v=False, ms=False, pr=False)
  return parser

def main(args):
  """Main function of the smatch calculation program"""
  global verbose
  global iter_num
  global single_score
  global pr_flag
  global match_num_dict
  # set the restart number
  iter_num = args.r + 1
  verbose = False
  if args.ms:
    single_score = False
  if args.v:
    verbose = True
  if args.pr:
    pr_flag = True
  total_match_num = 0
  total_test_num = 0
  total_gold_num = 0
  sent_num = 1
  prev_amr1 = ""
  outfile = open(args.outfile, 'w')
  if not single_score:     
    outfile.write("Sentence\tText")
    if pr_flag:
      outfile.write("\tPrecision\tRecall")
    outfile.write("\tSmatch\n")
    
  while True:
    cur_amr1 = smatch.get_amr_line(args.f[0])
    (cur_amr2, comments) = amr_metadata.get_amr_line(args.f[1])
    if cur_amr1 == "" and cur_amr2 == "":
      break
    if(cur_amr1 == ""):        
      # GULLY CHANGED THIS. 
      # IF WE RUN OUT OF AVAILABLE AMRS FROM FILE 1, 
      # REUSE THE LAST AVAILABLE AMR
      cur_amr1 = prev_amr1  
      #print >> sys.stderr, "Error: File 1 has less AMRs than file 2"
      #print >> sys.stderr, "Ignoring remaining AMRs"
      #break
      # print >> sys.stderr, "AMR 1 is empty"
      # continue
    if(cur_amr2 == ""):
      print >> sys.stderr, "Error: File 2 has less AMRs than file 1"
      print >> sys.stderr, "Ignoring remaining AMRs"
      break
    # print >> sys.stderr, "AMR 2 is empty"
    # continue
    prev_amr1 = cur_amr1
    
    amr1 = amr.AMR.parse_AMR_line(cur_amr1)
    amr2 = amr.AMR.parse_AMR_line(cur_amr2)
    
    # We were getting screwy SMATCH scores from 
    # using the amr_metadata construct
    meta_enabled_amr = amr_metadata.AmrMeta.from_parse(cur_amr2, comments)
    
    test_label = "a"
    gold_label = "b"
    amr1.rename_node(test_label)
    amr2.rename_node(gold_label)
    (test_inst, test_rel1, test_rel2) = amr1.get_triples2()
    (gold_inst, gold_rel1, gold_rel2) = amr2.get_triples2()
    if verbose:
      print "AMR pair", sent_num
      print >> sys.stderr, "Instance triples of AMR 1:", len(test_inst)
      print >> sys.stderr, test_inst
  #   print >> sys.stderr,"Relation triples of AMR 1:",len(test_rel)
      print >> sys.stderr, "Relation triples of AMR 1:", len(test_rel1) + len(test_rel2)
      print >>sys.stderr, test_rel1
      print >> sys.stderr, test_rel2
  #   print >> sys.stderr, test_rel
      print >> sys.stderr, "Instance triples of AMR 2:", len(gold_inst)
      print >> sys.stderr, gold_inst
  #   print >> sys.stderr,"Relation triples of file 2:",len(gold_rel)
      print >> sys.stderr, "Relation triples of AMR 2:", len(
          gold_rel1) + len(gold_rel2)
      #print >> sys.stderr,"Relation triples of file 2:",len(gold_rel1)+len(gold_rel2)
      print >> sys.stderr, gold_rel1
      print >> sys.stderr, gold_rel2
  #    print >> sys.stderr, gold_rel
    if len(test_inst) < len(gold_inst):
      (best_match,
       best_match_num) = smatch.get_fh(test_inst,
                                test_rel1,
                                test_rel2,
                                gold_inst,
                                gold_rel1,
                                gold_rel2,
                                test_label,
                                gold_label)
      if verbose:
        print >> sys.stderr, "AMR pair ", sent_num
        print >> sys.stderr, "best match number", best_match_num
        print >> sys.stderr, "best match", best_match
    else:
      (best_match,
       best_match_num) = smatch.get_fh(gold_inst,
                                gold_rel1,
                                gold_rel2,
                                test_inst,
                                test_rel1,
                                test_rel2,
                                gold_label,
                                test_label)
      if verbose:
        print >> sys.stderr, "Sent ", sent_num
        print >> sys.stderr, "best match number", best_match_num
        print >> sys.stderr, "best match", best_match
    if not single_score:
      #(precision,
      # recall,
      # best_f_score) = smatch.compute_f(best_match_num,
      #                           len(test_rel1) + len(test_inst) + len(test_rel2),
      #                           len(gold_rel1) + len(gold_inst) + len(gold_rel2))
      outfile.write( str(meta_enabled_amr.metadata.get("tok", None)) )
      #if pr_flag:
      #  outfile.write( "\t%.2f" % precision )
      #  outfile.write( "\t%.2f" % recall )
      #outfile.write( "\t%.2f" % best_f_score )
      print sent_num
      outfile.write( "\n" )
    total_match_num += best_match_num
    total_test_num += len(test_rel1) + len(test_rel2) + len(test_inst)
    total_gold_num += len(gold_rel1) + len(gold_rel2) + len(gold_inst)
    match_num_dict.clear()
    sent_num += 1  # print "F-score:",best_f_score
  if verbose:
    print >> sys.stderr, "Total match num"
    print >> sys.stderr, total_match_num, total_test_num, total_gold_num
  if single_score:
    (precision, recall, best_f_score) = smatch.compute_f(
        total_match_num, total_test_num, total_gold_num)
    if pr_flag:
      print "Precision: %.2f" % precision
      print "Recall: %.2f" % recall
    print "Document F-score: %.2f" % best_f_score
  args.f[0].close()
  args.f[1].close()
  outfile.close()

if __name__ == "__main__":
  parser = None
  args = None
  if sys.version_info[:2] != (2, 7):
    if sys.version_info[0] != 2 or sys.version_info[1] < 5:
      print >> ERROR_LOG, "Smatch only supports python 2.5 or later"
      exit(1)
    import optparse
    if len(sys.argv) == 1:
      print >> ERROR_LOG, "No argument given. Please run smatch.py -h to see the argument descriptions."
      exit(1)
    # requires version >=2.3!
    parser = build_arg_parser2()
    (args, opts) = parser.parse_args()
    # handling file errors
    # if not len(args.f)<2:
    #   print >> ERROR_LOG,"File number given is less than 2"
    #   exit(1)
    file_handle = []
    if args.f is None:
      print >> ERROR_LOG, "smatch.py requires -f option to indicate two files containing AMR as input. Please run smatch.py -h to see the argument descriptions."
      exit(1)
    if not os.path.exists(args.f[0]):
      print >> ERROR_LOG, "Given file", args.f[0], "does not exist"
      exit(1)
    else:
      file_handle.append(codecs.open(args.f[0], encoding='utf8'))
    if not os.path.exists(args.f[1]):
      print >> ERROR_LOG, "Given file", args.f[1], "does not exist"
      exit(1)
    else:
      file_handle.append(codecs.open(args.f[1], encoding='utf8'))
    args.f = tuple(file_handle)
  else:  # version 2.7
    import argparse
    parser = build_arg_parser()
    args = parser.parse_args()
  main(args)
