# coding=utf-8
#
# Run initial clones from a local cache to save on network traffic
#
#   Copyright 2014 Tikitu de Jager <tikitu@logophile.org>
#
# This software may be used and distributed according to the terms of the
# GNU General Public License version 2 or any later version.

import mercurial
from mercurial import cmdutil, commands, hg
from mercurial import ui as uimod
from mercurial.util import url
from mercurial.i18n import _
import urllib
import os.path

testedwith = '3.2'
__version__ = '0.0.4'


cmdtable = {}

command = cmdutil.command(cmdtable)

CACHE = os.path.expanduser('~/.hg.cache')


@command(
    'cache',
    [('', 'update', None, _('update all cached repos')),
    ],
    _('[OPTION]... [SOURCE]...'),
    norepo=True
)
def cache_cmd(ui, source=None, **opts):
    if source is None and not opts.get('update'):
        raise hg.util.Abort(_("either SOURCE or --update is required"))
    print source
    if opts.get('update'):
        for repo_d in os.listdir(CACHE):
            if source is None or repo_d == url_to_filename(source):
                ui.status('updating cache {}\n'.format(repo_d))
                cache_peer = hg.peer(ui, {}, os.path.join(CACHE, repo_d))
                commands.pull(cache_peer.ui, cache_peer.local(), noupdate=True)
    else:
        if hg.islocal(source):
            raise hg.util.Abort(_("not caching local repo {}".format(source)))
        cache_d = os.path.join(CACHE, url_to_filename(source))
        ui.status(_('caching {} to {}\n'.format(source, cache_d)))
        commands.clone(ui, source, cache_d, noupdate=True)


@command('clone',
    [('U', 'noupdate', None,
     _('the clone will include an empty working copy (only a repository)')),
    ('u', 'updaterev', '', _('revision, tag or branch to check out'), _('REV')),
    ('r', 'rev', [], _('include the specified changeset'), _('REV')),
    ('b', 'branch', [], _('clone only the specified branch'), _('BRANCH')),
    ('', 'pull', None, _('use pull protocol to copy metadata')),
    ('', 'uncompressed', None, _('use uncompressed transfer (fast over LAN)')),
    ('', 'nocache', None, _('Ignore the cache')),
    ] + commands.remoteopts,
    _('[OPTION]... SOURCE [DEST]'),
    norepo=True)
def clone_cache_cmd(ui, source, dest=None, **opts):
    source_url = url(source)
    if source_url.fragment is not None:
        raise ValueError('Someone is being clever! We are not clever. Bail.')

    orig_source = source
    cache_source = os.path.join(CACHE, url_to_filename(source))
    was_cached = False
    clone_source = source
    if not opts.get('nocache'):
        was_cached = os.path.exists(cache_source)
        if was_cached:
            ui.status('cloning from cache {}\n'.format(cache_source))
            clone_source = cache_source
            if dest is None:
                dest = hg.defaultdest(source)
        else:
            ui.status('no cache found at {}, cloning from source {}\n'.format(
                cache_source, source))
    
    if opts.get('noupdate') and opts.get('updaterev'):
        raise util.Abort(_("cannot specify both --noupdate and --updaterev"))

    r = hg.clone(ui, opts, clone_source, dest,
                 pull=opts.get('pull'),
                 stream=opts.get('uncompressed'),
                 rev=opts.get('rev'),
                 update=opts.get('updaterev') or not opts.get('noupdate'),
                 branch=opts.get('branch'))

    if r is None:
        return True

    source_peer, dest_peer = r

    if was_cached:
        dest_repo = dest_peer.local()
        if dest_repo:
            orig_source = dest_repo.ui.expandpath(orig_source)
            abspath = orig_source
            if hg.islocal(orig_source):
                abspath = os.path.abspath(hg.util.urllocalpath(orig_source))

            u = url(abspath)
            u.passwd = None
            defaulturl = str(u)
            fp = dest_repo.opener("hgrc", "w", text=True)
            fp.write("[paths]\n")
            fp.write("default = %s\n" % defaulturl)
            fp.write('\n')
            fp.write('[clonecache]\n')
            fp.write('cache = %s\n' % cache_source)
            fp.close()

            dest_repo.ui.setconfig('paths', 'default', defaulturl, 'clone')

            commands.pull(dest_repo.ui, dest_repo)

            commands.update(ui, dest_repo)

    return False


def url_to_filename(url):
    return urllib.quote_plus(url)
