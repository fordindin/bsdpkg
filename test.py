#!/usr/local/bin/python -O

from bsdpkg import PkgVersion,Package,PkgCache
import bsdpkg
#from pkgraph import PkGraph
import sys

"""
a = PkgVersion("ruby-1.8.6.160_3,1")

a = PkgVersion("ruby-1.8.6.160_3,2")

a = PkgVersion("ruby-1.8.3.161_3")

a = PkgVersion("ruby-1.8.3.161_2")

a = PkgVersion("ruby-1.8.7.160,1")

a = PkgVersion("rb-ruby-1.8.7.160,1")
"""

#print PkgVersion("rb-ruby-1.8.7.160,1") == PkgVersion("rb-ruby-1.8.7.160,2")
#print PkgVersion("rb-ruby-1.8.7.160,1") > PkgVersion("rb-ruby-1.8.7.160,2")


''' pkg comparation '''
if sys.argv[1] == "ver":
    print PkgVersion("rb-ruby-1.8.7.160,1") == PkgVersion("rb-ruby-1.8.7.160,1")
    print PkgVersion("rb-ruby-1.8.7.160,1") != PkgVersion("rb-ruby-1.8.7.160,1")
    print PkgVersion("rb-ruby-1.8.7.3_2,2") > PkgVersion("rb-ruby-1.8.7.160,2")
    print PkgVersion("rb-ruby-1.8.7.3_2,2") < PkgVersion("rb-ruby-1.8.7.160,2")
    print PkgVersion("rb-ruby-1.8.7.160,2") > PkgVersion("rb-ruby-1.8.7.3_2,2")
    print PkgVersion("rb-ruby-1.8.7.160,2") < PkgVersion("rb-ruby-1.8.7.3_2,2")
    print PkgVersion("rb-ruby-r1230") > PkgVersion("rb-ruby-r232")
    print PkgVersion("rb-ruby-r1230") < PkgVersion("rb-ruby-r232")
    p=PkgVersion("rb-ruby-1.8.7.160,1")
    print str(PkgVersion("rb-ruby-1.8.7.160,2"))


''' pkgcache operations '''
if sys.argv[1] == "cache":
    c = PkgCache();
    for p in c.pkglist():
        print p.name
    print c._garbage
    c.cleanup()

if sys.argv[1] == "graph":
    g = PkGraph(directed=True, rootnode="1")
    #g.delete_vertices(0)

    #root = g.add_vertex("1")

    g.add_vs_ln_to_parent("1","2-1")
    g.add_vs_ln_to_parent("1","2-2")
    g.add_vs_ln_to_parent("1","2-3")

    g.add_vs_ln_to_parent("2-1","2-1-1")
    g.add_vs_ln_to_parent("2-1","2-1-2")
    g.add_vs_ln_to_parent("2-1","2-1-3")

    g.add_vs_ln_to_parent("2-2","2-2-1")

    g.add_vs_ln_to_parent("2-2-1","2-2-1-1")
    g.add_vs_ln_to_parent("2-2-1","2-2-1-2")

    g.add_vs_ln_to_parent("2-2","2-2-2")
    g.add_vs_ln_to_parent("2-2","2-2-3")

    """
    for v in g.vs:
      print (
              g.strength(v, weights="weight",type=igraph.OUT),
              g.strength(v, weights="weight",type=igraph.IN),
              v[VID],
              g.get_vs_ix_by_vid(v[VID])
              )
    """

    print g.full_reverse_order()

if sys.argv[1] == "mgr":
    #g = build_pkgraph("ctags-5.8")
    #g = ("ctags-5.8")
    #print g.full_reverse_order()
#    pkg = Package(None,
#            path="/home/dindin/tmp/tmp/p5-String-CRC32-1.4.tbz")

    #bsdpkg.SHORT_REPO_URL="https://distillatory.yandex.ru/pub/FreeBSD/ports/amd64/packages-8-stable/Latest"
    cache=PkgCache(cache_dir_base="/tmp/cache", repo_ident="8.1-FBSD_20101028")
    #cache.reread()
    #cache.cache(pkg)
    #print pkg.__dict__

    #pkg = Package(None,path="/tmp/cache/bash.tbz", cacheobj=cache)
    pkg = Package("bash",
            cache=cache)

    print pkg.version.__dict__
    #print pkg.version.__dict__

    pkg.recursive()
    #print pkg.origin

    #print pkg.install(prefix="/tmp/temproot/")
    #g = PkGraph(rootnode=pkg.name)
    #g.recurse_pkgraph(cache,pkg)
    #print g.full_reverse_order()
    #print pkg.install(prefix="/tmp/temproot/")

    """
    """

    #cache.drop()
    #cache.reread()

if sys.argv[1] == "compile": pass

if sys.argv[1] == "rtest":
    print PkgVersion("nvramtool-r6440").__dict__

if sys.argv[1] == "bugfix": 
    #print PkgVersion("someshit-8.00")
    print PkgVersion("mrapps-r123545") < PkgVersion("mrapps-r123546")
    print "mrapps-r1235.45.12a_7,9"
    print PkgVersion("mrapps-r1235.45.12a_7,9")
    print PkgVersion("mc-light-4.1.40.p9_7")
    print PkgVersion("mc-light-4.1.40.p8_7") > PkgVersion("mc-light-4.1.40.p9_7")
    print PkgVersion("mc-light-4.1.40.p8_7") == PkgVersion("mc-light-4.1.40.p9_7")
    print PkgVersion("mc-light-4.1.40.p8_7") < PkgVersion("mc-light-4.1.40.p9_7")
    print PkgVersion("mc-light-4.1.45.p8_7") < PkgVersion("mc-light-4.1.40.p9_7")
    print PkgVersion("mc-light-4.1.45.p8_7") > PkgVersion("mc-light-4.1.40.p9_7")
    """
    """

