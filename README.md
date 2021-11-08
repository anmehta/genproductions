# genproductions
Generator fragments for MC production

The package includes the datacards used for various generators inclusing POWHEG, MG5_aMC@NLO, Sherpa, Phantom, Pythia...

Further details are reported in the twiki: https://twiki.cern.ch/twiki/bin/view/CMS/GeneratorMain#How_to_produce_gridpacks

Instructions on how to use the fragments are here https://twiki.cern.ch/twiki/bin/view/CMS/GitRepositoryForGenProduction

# Unimib EFT gridpack production

This repo contains centrall tools to produce gridpacks (genprocutions) along with custom EFT tools to produce EFT gridpacks with SMEFTsim.

# Gridpacks

A MG folder which has been optimised for batch-mode computation. The MadGraph "single-diagrams-enhanched multichannel" integration technique makes it possible to split the phase space integration into small bits that can be evaluated independently. The expolitation of a fully parallel compututational workflow allows to reduce the time required to obtain a MG folder by order of magnitudes.
MG gridpack computation is split in two(three) steps: CODEGEN, INTEGRATE (MADSPIN), where madspin is not mandatory. 
- CODEGEN: code generation step, finds processes / subprocesses and diagrams
- INTEGRATE: phase space integration
- MADSPIN: decay of particles accounting for spin, offshell eccets, ...

# Generate gridpacks with EFT contributions
## SMEFTsim compressed UFO

EFT contributions are simulated at LO via SMEFTsim (https://smeftsim.github.io/).
A ready-to-go version of SMEFTsim UFO model with U35 flavour scheme and mW,mZ,Gf input scheme is publicly accessible at http://gboldrin.web.cern.ch/gboldrin/generators/SMEFTsim_U35_MwScheme_UFO.tar.gz 
This version is up to date as of 8th November 2021 and also contains restriction cards for 15 operators (cW,cHW,cHbox,cHDD,cHWB,cHl1,cHl3,cHq1,cHq3,cll,cll1,cqq1,cqq3,cqq11,cqq31) both for single insertion or for all the posssible pairs. The directory also contain custom restriction cards to activate all operators at the same time or a subset of them e.g. http://gboldrin.web.cern.ch/gboldrin/generators/restrict_cW_cHWB_cHDD_cHbox_cHW_cHl1_cHl3_cHq1_cHq3_cqq1_cqq11_cqq31_cqq3_cll_cll1_massless.dat	

If you need a more up to date version of SMEFTsim or different restriction cards, it is highly suggested to clone a copy of SMEFTsim, build the restrictions you need, move them under the UFO model, pack everything again and copy the compressed folder on your web area (e.g. /eos/user/y/yourusername/www on lxplus).

- Create a tar version of SMEFTsim with restriction cards

```
git clone git@github.com:SMEFTsim/SMEFTsim.git
mv SMEFTsim/UFO_models/SMEFTsim_MFV_alphaScheme_UFO . # choose the UFO model you need
cp SMEFTsim_MFV_alphaScheme_UFO/restrict_SMlimit_massless.dat restrict_your_set_of_op_massless.dat #copy SM restriction 
#Modify restrict_your_set_of_op_massless.dat turning on and off operators under SMEFT or SMEFTFV blocks (on = 9.999999e-01, off = 0)
tar -zcvf SMEFTsim_MFV_alphaScheme_UFO.tar.gz SMEFTsim_MFV_alphaScheme_UFO
xrdcp SMEFTsim_MFV_alphaScheme_UFO.tar.gz /eos/user/y/yourusername/www
```

Examples of restriction cards (and script to automate the cards generation) can be found at https://github.com/UniMiBAnalyses/D6EFTStudies/tree/master/madgraph_model/v3_0 (https://github.com/UniMiBAnalyses/D6EFTStudies/blob/master/madgraph_model/buildRestrict_v3_0.py)


## Lxplus or CMSConnect

Gridpack generation can be done both on lxplus or cmsconnect as both have HTCondor to submit batch jobs. However, part of the gridpack will still run in local.
A lxplus worker node has 10 cores while cmsconnect has 48. You will be 5 times quicker while working on cmsconnect than lxplus.
Some comments:
- Never work fully local on cmsconnect. If you overload the system your jobs will be killed (e.g. if you submit multiple gridpacks creation in parallel).
- You can work fully local on lxplus, at least, you will hardly find resource issues.

Follow this tutorial on how to subscribe to cmsconnect:
https://indico.cern.ch/event/615524/contributions/2520456/attachments/1430441/2197104/March20_2017_gen_meeting.pdf

## EFT gridpack submission scripts overview and clarifications

Once you decided if you'll generate your MG gridpack on lxplus or cmsconnect, simply login, go to the desired working folder and clone this repo (check if this repo is up to date). If needed, change branch but scripts only work for master as of 8/11/2021:

```
git clone git@github.com:UniMiBAnalyses/genproductions.git && cd genproductions/bin/MadGraph5_aMCatNLO/

```

The main script is: `gridpack_generation_EFT.sh` which is a copy of `gridpack_generation.sh` with some lines added to it:

```
245       wget --no-check-certificate http://gboldrin.web.cern.ch/gboldrin/generators/SMEFTsim_U35_MwScheme_UFO.tar.gz
246       cd models
247       tar xavf ../SMEFTsim_U35_MwScheme_UFO.tar.gz
248       cd SMEFTsim_U35_MwScheme_UFO
249       # wget all restrictions
250       wget --no-check-certificate http://gboldrin.web.cern.ch/gboldrin/generators/restrict_cHWB_cHDD_cHl1_cHl3_cHq1_cHq3_cll_cll1_massless.dat
251       wget --no-check-certificate http://gboldrin.web.cern.ch/gboldrin/generators/restrict_cW_cHWB_cHDD_cHl1_cHl3_cHq1_cHq3_cll_cll1_massless.dat
252       wget --no-check-certificate http://gboldrin.web.cern.ch/gboldrin/generators/restrict_cW_cHWB_cHDD_cll1_cHl1_cHl3_cHq1_cHq3_massless.dat
253       wget --no-check-certificate http://gboldrin.web.cern.ch/gboldrin/generators/restrict_cW_cHWB_cHDD_cHbox_cHW_cHl1_cHl3_cHq1_cHq3_cqq1_cqq11_cqq31_cqq3_cll_cll1_massless.dat
254       cd ../.. 
```

If you need to generate from a different branch than master as of 8/11/2021, simply copy `gridpack_generation.sh` and add those lines. If you genrated your version of compressed SMEFTsim UFO model, simply replace this paths with yours.

Accessory scripts needs to be modified in order to run `gridpack_generation_EFT.sh` on condor: `submit_cmsconnect_gridpack_generation_EFT.sh`, `submit_condor_gridpack_generation_EFT.sh`. 
These are just copies of the same ones without `_EFT`suffix and few lines modified. If you need to work on another branch and not master as of 8/11/2021, simply copy `submit_cmsconnect_gridpack_generation.sh`, `submit_condor_gridpack_generation.sh` and replace `gridpack_generation.sh` with `gridpack_generation_EFT.sh` everywhere.


## Generate the gridpack

Once you have all necessary scripts you are ready to issue the generation:

```
./gridpack_generation_EFT.sh card_name path/to/cards # this runs locally 
```

Where path/to/cards contains the MG5 cards. Some are mandatory and must follow a naming convention: `card_name_proc_card.dat`, `card_name_run_card.dat`.
An accessory card will be needed for SMEFTsim: `card_name_customizecards.dat`, where you set the initial values for EFT coupling.
An additional card is mandatory if one want to use the reweight module: `card_name_reweight_card.dat`. 
**IMPORTANT**: You do not need an extramodel card, the script will always download the SMEFTsim tarball even if you won't need it.

Example of cards can be found under:

`cards/ZZ2e2mu/ZZ2e2mu_cW_cHWB_cHDD_cHbox_cHW_cHl1_cHl3_cHq1_cHq3_cqq1_cqq11_cqq31_cqq3_cll_cll1_SM_LI_QU_IN`

Where we generate a VBS ZZ process into 4 leptons of different flavour (2e, 2mu) with EFT contributions from 15 operators. We also use the reweight module to change hypothesis and turn off-on operators.

Following the ZZ example:
```
./gridpack_generation_EFT.sh ZZ2e2mu_cW_cHWB_cHDD_cHbox_cHW_cHl1_cHl3_cHq1_cHq3_cqq1_cqq11_cqq31_cqq3_cll_cll1_SM_LI_QU_IN cards/ZZ2e2mu/ZZ2e2mu_cW_cHWB_cHDD_cHbox_cHW_cHl1_cHl3_cHq1_cHq3_cqq1_cqq11_cqq31_cqq3_cll_cll1_SM_LI_QU_IN # this runs locally, should be avoided 

./submit_cmsconnect_gridpack_generation.sh ZZ2e2mu_cW_cHWB_cHDD_cHbox_cHW_cHl1_cHl3_cHq1_cHq3_cqq1_cqq11_cqq31_cqq3_cll_cll1_SM_LI_QU_IN cards/ZZ2e2mu/ZZ2e2mu_cW_cHWB_cHDD_cHbox_cHW_cHl1_cHl3_cHq1_cHq3_cqq1_cqq11_cqq31_cqq3_cll_cll1_SM_LI_QU_IN (n_cores) ("memory")

./submit_condor_gridpack_generation.sh ZZ2e2mu_cW_cHWB_cHDD_cHbox_cHW_cHl1_cHl3_cHq1_cHq3_cqq1_cqq11_cqq31_cqq3_cll_cll1_SM_LI_QU_IN cards/ZZ2e2mu/ZZ2e2mu_cW_cHWB_cHDD_cHbox_cHW_cHl1_cHl3_cHq1_cHq3_cqq1_cqq11_cqq31_cqq3_cll_cll1_SM_LI_QU_IN (n_cores) ("memory")
```

## Screen (or tmux)

Gridpacks usually take from O(h) to O(days) to be completed. It is unfeasible to stay connected for such a long time length. Screen (or tmux) are essential tools in order to issue commands and leave it running also after disconnecting from the ssh tunnel. Both lxplus and cmsconnect provide out of the box screen support:

```
screen # open a new scren session
screen -ls # list all open screen sessions on the worker node
screen -rD _ID_ # connect to a detached screen session with id = _ID_
```

After issuing the `screen` command a new shell will be opened. You can use it the same way as a normal terminal session. In order to detach from the screen session type `Ctrl + A + D`. You will be redirected to the shell in which the `screen`command wa issued and you can inspect the opened screen session:

```
[gboldrin@lxplus731 MadGraph5_aMCatNLO]$ screen -ls
There is a screen on:
	9358.pts-12.lxplus731	(Detached)
1 Socket in /var/run/screen/S-gboldrin.
```

`9358` is the session ID. To reconnect:

```
screen -rD 9358
screen -rD 9358.pts-12.lxplus731
```

**WARNING**:

There some differences between lxplus and cmsconnect regarding screen. On lxplus you usually log into a worker node (from the example above 731 machine) while on cmsconnect there is only one machine. If you open a screen session on lxplus and then detach from it and log out from the ssh, you'll need to store the machine number and reconnect to the same machine in order to retrive the screen session. From the example above:

```
ssh username@lxplus731.cern.ch
screen -rD 9358
```

Furthermore, the screen session on lxplus works with kerberos tokens which allow the session to have permission to write/read from your afs area. These tickets are created with the command `kinit` and authorised with your lxplus login password. The tickets last for 25 hours after ssh disconnection and there is no way to change that. After 25h the commands won't be able to, for example, read or create files in your user area.

One way to create a persistent screen session on lxplus is to create a keytab which automatically refresh your expired tickets.

From a private folder on your afs (e.g. `/afs/cern.ch/user/u/username/private`) type:

```
mkdir ktokens && ktutil
```

A new prompt will appear. Type in the prompt the following lines:

```
add_entry -password -p USERNAME@CERN.CH -k 1 -e arcfour-hmac-md5
add_entry -password -p USERNAME@CERN.CH -k 1 -e aes256-cts
wkt USERNAME.keytab
Ctrl+D #close ktutil session
```

`k5reauth` can now be used, it will issue user defined commands in a child process and will renew your kerberos tokes after N seconds also for the child itself.

Using the ZZ VBS example, this command will create a permanent screen session with renewable tokens once every 3600 seconds:

```
cd /path/to/genproductions/bin/MadGraph5_aMCatNLO/
k5reauth -f -i 3600 -p USERNAME -k /afs/cern.ch/user/u/username/private/ktokens/USERNAME.keytab -- screen ./submit_cmsconnect_gridpack_generation.sh ZZ2e2mu_cW_cHWB_cHDD_cHbox_cHW_cHl1_cHl3_cHq1_cHq3_cqq1_cqq11_cqq31_cqq3_cll_cll1_SM_LI_QU_IN cards/ZZ2e2mu/ZZ2e2mu_cW_cHWB_cHDD_cHbox_cHW_cHl1_cHl3_cHq1_cHq3_cqq1_cqq11_cqq31_cqq3_cll_cll1_SM_LI_QU_IN
```

You can also create an alias for this command in your `.bash_profile` or `.bashrc`

```
kscreen(){
    if [[ -z "$1" ]]; then #if no argument passed
        echo "First argument must be the executable name"
    else #pass the argument to screen
        k5reauth -f -i 3600 -p USERNAME -k /afs/cern.ch/user/u/username/private/ktokens/USERNAME.keytab  -- screen $1
    fi
}
```

and use it as a normal screen session:

`
kscreen ./submit_cmsconnect_gridpack_generation.sh ZZ2e2mu_cW_cHWB_cHDD_cHbox_cHW_cHl1_cHl3_cHq1_cHq3_cqq1_cqq11_cqq31_cqq3_cll_cll1_SM_LI_QU_IN cards/ZZ2e2mu/ZZ2e2mu_cW_cHWB_cHDD_cHbox_cHW_cHl1_cHl3_cHq1_cHq3_cqq1_cqq11_cqq31_cqq3_cll_cll1_SM_LI_QU_IN
`


# Problems

It may happen that a gridpack runs smoothly in local (`gridpack_generation_EFT.sh`) while it will crash in batch mode (`submit_cmsconnect_gridpack_generation.sh` or `submit_condor_gridpack_generation.sh`). It is suggested to look at the run card of your process.
If working with the master branch as of 8/11/2021 (MG5_2_6_5) then try to simply copy the run card `cards/ZZ2e2mu/ZZ2e2mu_cW_cHWB_cHDD_cHbox_cHW_cHl1_cHl3_cHq1_cHq3_cqq1_cqq11_cqq31_cqq3_cll_cll1_SM_LI_QU_IN/*_run_card.dat` under your process dirctory and issue the batch submission again. If the generation runs fine, simply modify the run card as you need.




