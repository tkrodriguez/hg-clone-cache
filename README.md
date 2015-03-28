# hg-clone-cache

Patch mercurial `hg clone` to first check a local cache before hitting network. Adds the command `hg cache <url>` to add (remote) repos to the cache.

## Warning #1

This code has no tests. You know what that means: don't trust it with anything you value. It was hacked together on 
an airplane flight and is not of very high quality.

## Warning #2

This extension *modifies the `hg clone` command*. If you don't need it, don't leave it enabled. (To disable an 
extension, prefix its path with `!` in your `.hgrc` file, or remove it entirely from the file.)

## Warning #3

Mercurial version 2.9 only. That's quite likely not what you're running. (It's what I targeted because that's what 
my work dev-tools package bundles.)

## So what does it actually *do*?

It adjusts the `hg clone` command so that when you clone a remote repository. it will first look in a *cache 
directory* (`~/.hg.cache`) to see if you have a clone of that repository already cached. If you do, it performs
a local clone (much faster than accessing the network if the repo has lots of history!). It adjusts the `.hg/hgrc` 
file to point to the repo you wanted to clone (not the copy in the local cache), then performs a `pull` and `update`
in case the local cache clone is out of date.

In short: cloning a remote repo that you have already cached should be faster and involve less network traffic.

To get repos into your cache, the extension adds a new command `hg cache <url>` which does just what you would
expect. You can also issue `hg cache --update` to pull changes into *all* repos in your cache. (Why would you bother?
Well, only the changesets you have in the cache are cloned locally: everything else still has to come over the 
network. If you let your cache get far out of date, you're not getting as much benefit from it as you could.)

## When would I find this really really useful?

It helps if you're frequently making clones of the same remote repos. The author uses `zc.buildout` and 
`mr.developer` rather heavily, and these tools clone the same core set of repos on a near-daily basis.

You also have to care about download speeds. The author accesses said remote repos from a different timezone via a
VPN connection that seems to throttle bandwidth (although nobody can say how or why). If you have a "fat pipe" (is
that what they call it?) you probably don't need this so much.

## I'm convinced: how do I install it?

Put it somewhere on your pythonpath (e.g. by cloning this repository), and [enable the extension in your 
`.hgrc`](http://mercurial.selenic.com/wiki/UsingExtensions). Mine looks like this:

    [extensions]
    clonecache = ~/code/hg-clone-cache/clonecache.py

### Why only remote repos?

Because the caching keys off the URL, and local paths can be relative. If I weren't so lazy I would expand them 
to full URLs (i.e. `file://` and absolute paths) and everything would Just Work, but I've scratched my itch. Pull
requests welcome.
