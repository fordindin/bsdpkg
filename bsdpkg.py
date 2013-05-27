#!/usr/bin/env python

import tarfile
import os, re, sys, time
import operator
import tarfile
import hashlib
import shutil
from urllib import URLopener
#from pkgraph import PkGraph, VID
import pickle
import subprocess

class BadPackage(Exception): pass
class BadPkgVersion(Exception): pass
class PkgBaseDiffers(Exception): pass
class CachePathError(Exception): pass
class PkgUnfetchable(Exception): pass

PATH=0
CACHE=1
URL=2
FILE=3

DEBUG=True
DEBUG=False

#REPO_BASE_URL="https://distillatory.yandex.ru/packages"
#SHORT_REPO_URL="https://distillatory.yandex.ru/pub/FreeBSD/ports/amd64/packages-7-stable/Latest"

class CacheEntry:
    def __init__(self, name, path):
        self.name=name
        self.path=path

class PkgCache:
    def __init__(self, cache_dir_base="/Berkanavt/tmp",
            repo_ident="FBSD_20100115", cache_tmp=None):

        self.repo_ident = repo_ident
        self.cache_dir_base = cache_dir_base
        if not cache_tmp: self.cache_tmp=cache_dir_base
        self.dumpname="cachedump"

        self.cachepath=os.path.join(self.cache_dir_base,"pkg.%s" %
                hashlib.md5(self.repo_ident).hexdigest())

        if os.access(os.path.join(self.cachepath,self.dumpname),\
                os.R_OK):
            f = open(os.path.join(self.cachepath, self.dumpname),
                "rb")
            p = pickle.load(f)
            self.__dict__.update(p.__dict__)
            f.close()
        else:
            if os.path.isdir(self.cachepath):
                if not os.access(self.cachepath,os.W_OK):
                    raise CachePathError("Can't write to directory" %
                            self.cachepath)
            else:
                os.mkdir(self.cachepath)

            self.packages = self.reread()

    def pkglist(self):
        return self.packages

    def pkgnames(self):
        return [ p.name for p in self.packages ]

    def reread(self):
        self._pkfiles=filter(lambda p: re.match("(.*).tbz",p),
                [ f for f in
                    os.listdir(self.cachepath)])

        self._garbage=filter(lambda p: not re.match("(.*).tbz",p) and
                not re.match("cachedump",p),
                [ f for f in
                    os.listdir(self.cachepath)])

        self.packages=[ Package(p, self.pkgpath(p.replace(".tbz",""))) \
                                                for p in self._pkfiles ]
        self.dump()
        return self.packages

    def cleanup(self):
        for f in self._garbage:
            os.remove(f)

    def package(self, pkgname):
        for p in self.packages:
            if pkgname == str(p.version):
                return p
            elif pkgname == p.version.pkgbase:
                return p
        return None

    def cache(self, pkg):
        targetpath = os.path.join(self.cachepath,str(pkg.version)+".tbz")
        if pkg.path and pkg.path != targetpath:
            shutil.copy(pkg.path, targetpath)
            if os.path.commonprefix([pkg.path, targetpath]).rstrip("/") \
                != self.cachepath.rstrip("/"): os.remove(pkg.path)
        pkg.path = targetpath
        self.packages.append(pkg)
        self.dump()
        #self.reread()

    def pkgpath(self, pkgname):
        return os.path.join(self.cachepath,"%s.tbz" % pkgname)

    def dump(self):
        f = open(os.path.join(self.cachepath,self.dumpname), "wb")
        pickle.dump(self, f)
        f.close()

    def drop(self):
        def rm(e,path,files):
            for f in files:
                os.remove(os.path.join(path,f))
        os.path.walk(self.cachepath,rm,None)
        os.removedirs(self.cachepath)

class PkgVersion:
    def __init__(self, versionstr):
        epoch_re = ''
        revision_re = ''
        patchlevel_re = ''

        try: epoch = int(re.findall(".*,([0-9]+)",versionstr)[0])
        except IndexError: epoch=None

        if epoch: epoch_re = ",%s" % epoch

        try: revision = int(re.findall(".*_([0-9]+)%s" % epoch_re, versionstr)[0])
        except IndexError: revision=None

        if revision: revision_re = "_%s" % revision

        try: patchlevel = int(re.findall("\.p([0-9]+)%s%s" %
            (revision_re, epoch_re), versionstr)[0])
        except IndexError: patchlevel=None

        if patchlevel: patchlevel_re = "\.p%s" % patchlevel

        pvr = "(.*)-([r]?[0-9.]+[a-dA-D]?)%s%s%s" % (patchlevel_re, revision_re, epoch_re)

        try: pkgbase, version = re.findall(pvr, versionstr)[0]
        except IndexError: raise BadPkgVersion("Can't parse package string: %s" % (versionstr))

        self.pkgbase = pkgbase
        tmp_match = re.findall("((?:\d+)|(?:[a-zA-Z]+))", version)
        self.version = [ PkgVersion.v_convert(v) for v in tmp_match ]
        self.npos = [ len(v) for v in tmp_match ]

        self.epoch = epoch
        self.revision = revision
        self.patchlevel = patchlevel
        self.pkgver= ""
        verpos= zip (self.version,self.npos)

        if re.match("%s-r[0-9]" % pkgbase, versionstr):
            self.pkgver+="r"

        for v in verpos:
            if type(v[0]) != type(""):
                tmp_tmpl = "%%0%dd" % v[1]
                self.pkgver+= tmp_tmpl % v[0] + "."
            else:
                pass
                #self.pkgver = self.pkgver.rstrip(".")
                #self.pkgver+=v[0] + "."
        print self.pkgver

        self.pkgver=self.pkgver.rstrip(".")
        if self.patchlevel: self.pkgver+=".p%s" % self.patchlevel
        if self.revision: self.pkgver+="_%s" % self.revision
        if self.epoch: self.pkgver+=",%s" % self.epoch

    def __str__(self):
        return self.pkgbase+"-"+self.pkgver

    def _comp(self, p, cfunction):
        if ( self.pkgbase != p.pkgbase):
            raise PkgBaseDiffers(
                    "comparasion between '%s' and '%s' failed" \
                            % (self.pkgbase, p.pkgbase))

        if (cfunction(self.epoch,p.epoch)) \
            or (cfunction(self.version,p.version)) \
            or (cfunction(self.revision,p.revision) \
            or (cfunction(self.patchlevel,p.patchlevel)) \
            and self.version == p.version): return True
        return False

    def __gt__(self,p):
        return self._comp(p,operator.gt)

    def __ge__(self,p):
        return self._comp(p,operator.gt)

    def __le__(self,p):
        return self._comp(p,operator.le)

    def __lt__(self,p):
        return self._comp(p,operator.lt)

    def __eq__(self, p, cfunction=None ):
        if not cfunction: cfunction = operator.eq
        if self.pkgbase != p.pkgbase:
            return False
        if cfunction(self.epoch,p.epoch) \
            and cfunction(self.version,p.version) \
            and cfunction(self.pkgbase,p.pkgbase) \
            and (cfunction(self.patchlevel,p.patchlevel)) \
            and cfunction(self.revision,p.revision): return True
        return False

        def __ne__(self,p):
                self.__eq__(p, cfunction=operator.ne)
                return False

    @staticmethod
    def v_convert(i):
        if i.isdigit():
            return int(i)
        return i

class Package:
    def __init__(
            self,
            name,
            path=None,
            cache=None,
            repo_ident="FBSD_20100115",
            pkgroot="https://distillatory.yandex.ru",
            branch_name="7-stable",
            arch="amd64",
            ):
        self._debug("%s %s" % ( name, path))
        self.cache=cache
        self.path = path

        self.repo_ident=repo_ident
        self.repo_base_url = "%s/packages" % pkgroot
        self.short_repo_url = "%s/pub/FreeBSD/ports/%s/packages-%s/Latest" % (
                pkgroot, arch, branch_name)

        self.pkgroot=pkgroot
        self.branch_name=branch_name
        self.arch=arch
        try:
            if name: PkgVersion(name)
            if path:
                if cache:
                    if not self.__init_from_cache(name):
                        if re.match("(http)|(https)|(ftp)://[0-9a-zA-Z./?&-_:@]+", path):
                            self.__init_from_url(path)
                        else:
                            self.__init_from_path(path)

            if name and not path and cache:
                if name in self.cache.pkgnames():
                    self.__init_from_cache(name)
                else:
                    self.__init_from_repo(name)
            elif name and not path and not cache:
                self.__init_from_repo(name)
        except BadPkgVersion:
            self.__init_from_url(name, self.short_repo_url)

    def __init_from_path(self,path):
        self._debug("__init_from_path %s" % (path))
        try:
            tf = tarfile.open(path,mode="r:bz2").extractfile('+CONTENTS')
            c = tf.read()
        except EOFError:
            raise BadPackage("Package %s is invalid" % path)

        try:
            self.name=re.findall("@name (.*)",c)[0]
            self.origin = re.findall("@comment ORIGIN:(.*)",c)[0]
        except IndexError: raise BadPackage("Malformed package: %s"\
                % path)

        try:
            self.deplist = re.findall("@pkgdep (.*)",c)
            if type(self.deplist) == type(""):
                self.deplist = [self.deplist]
        except IndexError:
            self.deplist = []

        self.version=PkgVersion(self.name)
        if self.cache:
            self.cache.cache(self)

        #self.path=path

    def __init_from_url(self, name, url, nocache=False):
        if not self.cache: raise PkgUnfetchable(
                "cahce object not specified")
        self._debug("__init_from_url %s/%s.tbz" % (url, name))
        # and not self.__init_from_cache(name):
        if name not in self.cache.pkgnames():
            self._debug("package name %s" % name)
            path = os.path.join(self.cache.cachepath, "%s.tbz" % name)
            self._debug("path: %s" % path)
            try:
                getfile=URLopener().retrieve(
                        "%s/%s.tbz" % (url, name),
                        filename=path,
                        reporthook=None # reporthook(blocknum, bs, size)
                        )
            except IOError:
                raise PkgUnfetchable("Can't fetch package %s from %s" % \
                        ( name, url))

            self.path=path
            self.__init_from_path(os.path.join(self.cache.cachepath, "%s.tbz" % name))
            self.cache.cache(self)
            #self.__init_from_cache(name)


    def __init_from_repo(self,name):
        self._debug("__init_from_repo %s" % (name))
        self.__init_from_url(name, "%s/%s/%s" % (self.repo_base_url,
            self.cache.repo_ident, "All"))

    def __init_from_cache(self,name):
        self._debug("__init_from_cache %s" % (name))
        pkg=self.cache.package(name)
        if pkg:
            self.__dict__ = pkg.__dict__
        else:
            self.__init_from_repo(name)
        #self.__init_from_path(self.cache.pkgpath(name))

    def __eq__(self, pkg):
        if self.version == pkg.version:
            return True
        return False

    def __ne__(self, pkg):
        if self.version != pkg.version:
            return True
        return False

    def __gt__(self, pkg):
        if self.version > pkg.version:
            return True
        return False

    def __lt__(self, pkg):
        if self.version < pkg.version:
            return True
        return False

    def __ge__(self, pkg):
        if self.version >= pkg.version:
            return True
        return False

    def __le__(self, pkg):
        if self.version <= pkg.version:
            return True
        return False

    def recursive(self,test=False):
        for d in self.deplist:
            p = Package(d,
                    cache=self.cache,
                    repo_ident=self.repo_ident,
                    pkgroot=self.pkgroot,
                    branch_name=self.branch_name,
                    arch=self.arch,
                    )
            self._debug(d)
            p.recursive(test=True)

    def install(self, prefix=None, tmpdir=None):
        pflag=""
        env={}
        if tmpdir: env.update({"PKG_TMPDIR":tmpdir})
        if prefix: pflag="-p %s" % str(prefix)
        if self.cache: env.update({"PKG_PATH":self.cache.cachepath})
        """
        cmd = "/usr/sbin/pkg_add \
                --no-deps \
                %s \
                %s" % (pflag, self.path)
        """
        cmd = "/usr/sbin/pkg_add \
                %s \
                %s" % (pflag, self.path)

        proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                shell=True,
                env=env,
                )
        stdin, stdout = proc.communicate()
        err = proc.wait()

        return err,stdin,stdout

    def chrooted_install(self, chroot, tmpdir=None):
        pflag=""
        env={}
        if tmpdir: env.update({"PKG_TMPDIR":tmpdir})
        if self.cache: env.update({"PKG_PATH":self.cache.cachepath})

        cmd = "/usr/sbin/pkg_add \
                -C %s \
                %s" % (chroot, self.path)

        self._debug(cmd)
        proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                shell=True,
                env=env,
                )
        stderr, stdout = proc.communicate()
        err = proc.wait()

        return err,stderr,stdout

    @staticmethod
    def _debug(msg):
        if DEBUG: print msg
