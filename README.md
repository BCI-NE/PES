
# Package Description


This package implements the full version of the PES Pandemic Experiment Scenario (i.e. with EEG recordings present through Biosemi device).

PES is a complex and strategic decision-making "Pandemic" Experiment. In this experiment, users will be shown a map
that gives a description of the spread of a pandemic emergency situation in various locations within the map. Resources
(in terms, medicines, personnels) are allocated to few cities in the beginning. The user must allocate more resources to
new cities that are displayed on the map. The user must keep in mind that the resources are limited and handing over all
resources could mean that new cities (if displayed) might not get any resources.

In this experiment, two or more users (one or more of which might be an artificial agent) will take part in the
experiment simultaneously and each will make a decision at each trial.  Users will make decisions and express confidence
independently.  Then, a new display will appear showing each user the decision, confidence and also an iconic facial
expression summary.  For human participants, this iconic representation will be obtained from OpenFace data.  Artificial
agents will be endowed with computational forms of confidence and trust and their iconic "facial expression" will be
derived from these.  At the end of each sequence, each participant will indicate how much they trust other users.

The idea is to have each participant to run the experiment, with a common communication and synchronization
mechanism.  Hence, each participant will perform their side of the processing, sharing outputs and synchronizing between
each other.

CONFIG.PY       : Default config. Allows the game to be played by a User and 1 teammate.
CONFIG_AI.py    : AI agent and 1 teammate.
CONFIG_SOLO_AI  : AI agent alone.


Authors: BCI-NE Lab, University of Essex, UK



# Usage


This package is a self-contained executable python package.

It is intended to be run directly, as:

    python3 -m PES

If desired, it is possible to further wrap the whole package inside a zipfile (e.g. PES.zip). To execute in this form
without unzipping, simply add the zipfile to your PYTHONPATH first. E.g.

    export PYTHONPATH="PES.zip"
    python3 -m PES

You can run in parallel, in the same computer or a in the same network segment, other teammate instances:

    python3 -m PES --config config/alt/CONFIG_AI.py 


Unit Tests can be run by typing:

    python3 -m PES.tests

Before running, make sure that you have edited the experiment's CONFIG.py file, which resides in the 'config' directory,
to configure the experiment to be run as appropriate.



# Files

The package has the following structure:   

    PES/
    ├── analysis: Scripts to perform basic analysis of the results.
    ├── config  : Configuration files.
    ├── doc     : Module documentation
    ├── ext     : External scripts with code related with the AI Agents.
    ├── inputs  : Input files with the experiment patterns.
    ├── lib     : External libraries for electrophysiological signals and comm.
    ├── outputs : Experiment output files.
    ├── res     : Media resources.
    ├── src     : Source code
    └── tests   : Unit tests.
       

       

# Disclaimer

This provided source code and platform was created at the University of Essex as part of UK MOD sponsored research.  It is released
for informational purposes only.  The contents and products of this source code should not be interpreted as representing the views
of the UK MOD, nor should it be assumed that they reflect any current or future UK MOD policy.

