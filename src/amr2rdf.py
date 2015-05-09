import amr
import uuid
import sys

SCHEMA_PREFIX = 'amr:'
ENTITY_PREFIX = 'ent:'

usage='%s AMRFILE' % __file__

def get_amr_lines(input_f):
    amr_lines = []
    cur_meta, cur_amr = '', ''
    for line in input_f:
        if line[0] == '(' and len(cur_amr) != 0:
            cur_amr = ''
        if line.strip() == '':
            if cur_amr: amr_lines.append((cur_meta, cur_amr))
            cur_meta, cur_amr = '', ''
        elif line.strip().startswith('#'):
            cur_meta += line.strip() + '\n'
        else:
            cur_amr += line.strip()
    if cur_amr: amr_lines.append((cur_meta, cur_amr))
    return amr_lines

def type_to_iri(t):
    return t + '_' + str(uuid.uuid4()).replace('-', '')

def amr_to_rdf(input_f):
    result = \
"""@prefix    rdf:    <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix    amr:    <http://amr.isi.edu/class#> .
@prefix    ent:    <http://amr.isi.edu/entity#> .
"""

    amr_lines = get_amr_lines(input_f)
    count = 0
    
    for meta, line in amr_lines:
        count += 1
        result += '\n\n# ===== AMR %d =====\n%s\n' % (count, meta)
        
        amr_obj = amr.AMR.parse_AMR_line(line)
        (instances, self_props, relations) = amr_obj.get_triples2()
        
        node_types = {i[1] : i[2] for i in instances}
        node_iris = {i[1] : type_to_iri(i[1] + '_' + i[2]) for i in instances}
    
        for k in node_types.keys():
            result += '%s a %s .\n' % (ENTITY_PREFIX + node_iris[k], SCHEMA_PREFIX + node_types[k])
            
        result += '\n'
            
        for entry in self_props:
            result += '%s %s "%s" .\n' % (ENTITY_PREFIX + node_iris[entry[1]], SCHEMA_PREFIX + entry[0], entry[2]) 
            
        result += '\n'
        
        for entry in relations:
            result += '%s %s %s .\n' % (ENTITY_PREFIX + node_iris[entry[1]], SCHEMA_PREFIX + entry[0], ENTITY_PREFIX + node_iris[entry[2]])
    
    return result

def main(argv):
    if len(argv) < 2 or len(argv) > 4:
        print >> sys.stderr, 'Usage: %s' % usage
        return 1
    amrfile = open(argv[1], 'r')

    result = amr_to_rdf(amrfile)
    
    print result

    return 0
    
if __name__ == '__main__':
    sys.exit(main(sys.argv))
