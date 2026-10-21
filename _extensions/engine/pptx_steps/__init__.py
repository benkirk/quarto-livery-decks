"""The pptx post-render steps, one module each, run in order by ../pptx_post.py: a zip step's
run(parts, name) changes the deck's members in place, a python-pptx step's run(prs, ...) the open
Presentation. common.py reads the livery once (the engine's livery.py) and holds what the steps
share; measure.py measures text in its faces."""
