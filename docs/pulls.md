# Pulling changes from the original repo into your fork

## Human

I forked `ssh://git@codeberg.org/tb4/records.git` into my own repo `ssh://git@codeberg.org/tb4/pages.git`. Now the original repo has new commits. How do I get them into my fork?

## Assistant

Picture a river. The original repo sits **upstream**, your fork lives **downstream**. New commits are fresh water — it never flows down to you by itself, you have to open the channel.

Three steps, always the same:

1. Tell git where upstream is (once).
2. Fetch what's new.
3. Merge it into your branch.

## Human

Okay, step 1?

## Assistant

Run this once, inside your fork's clone:

```bash
git remote add upstream ssh://git@codeberg.org/tb4/records.git
```

A *remote* is just a saved address — like a contact in your phone. You already have one contact called `origin` (your fork, `ssh://git@codeberg.org/tb4/pages.git`). Now you added a second one called `upstream` (the original).

Check your contact list with:

```bash
git remote -v
```

## Human

Done. Step 2?

## Assistant

```bash
git fetch upstream
```

Fetch is the delivery truck: it drops the new commits at your door, but **nothing in your files changes yet**. The package is on the porch, unopened.

That's the safe part — you can fetch as often as you like, it never breaks anything.

## Human

And step 3 opens the package?

## Assistant

Exactly. Make sure you're on your `main` branch, then merge:

```bash
git switch main
git merge upstream/main
```

Merge is two streams joining into one river: your commits and their commits flow together into a single history.

If you haven't changed the same lines they did, git does this silently ("fast-forward" — like a zipper closing).

## Human

What if we *did* change the same lines?

## Assistant

Then you get a **merge conflict** — two cooks wrote different things on the same line of the recipe.

Git stops and marks the disputed lines in the file like this:

```
<<<<<<< HEAD
your version
=======
their version
>>>>>>> upstream/main
```

You edit the file, keep what should stay, delete the markers, then:

```bash
git add <the-file>
git commit
```

No panic needed: git never throws anything away during a conflict. It just waits for you to decide.

## Human

Is my fork on Codeberg updated now too?

## Assistant

Not yet — you merged in your *local* clone. Your fork on Codeberg is a separate copy, like a shelf in a warehouse. Send the result back up:

```bash
git push origin main
```

Now all three are in sync: upstream, your clone, and your fork.

## Human

Can I shorten fetch + merge?

## Assistant

Yes:

```bash
git pull upstream main
```

`pull` = `fetch` + `merge` in one command — the truck delivers *and* you open the package immediately.

The whole routine, whenever upstream has news:

```bash
git pull upstream main
git push origin main
```

Two lines. Water flows down from the source, and you pump it back up to your own reservoir.
