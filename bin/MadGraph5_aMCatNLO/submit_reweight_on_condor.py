import os 
import sys
import argparse
import copy
import subprocess
import time
from glob import glob
from operator import itemgetter


def precompile_rwgt_dir(madevent_path):
    print("Precompiling reweighting modules")

    orig = os.getcwd()
    os.chdir(madevent_path)
    
    for file in glob("rwgt/*/*/SubProcesses/P*"):
        print ("Compiling subprocess " + file)
        os.chdir(file)
        for i in [2, 3]:
            os.environ['MENUM'] = str(i)
            out = os.system("MENUM={i} make matrix{i}py.so >& /dev/null".format(i=i))   
            print("Library MENUM={} compiled with status {}".format(i, out))
        os.chdir(madevent_path)
    
    os.chdir(orig)
    
    return 

def make_tarball(WORKDIR, iscmsconnect, PRODHOME, CARDSDIR, CARDNAME, scram_arch, cmssw_version):
    print("---> Creating tarball")
    os.chdir("{WORKDIR}/gridpack".format(WORKDIR=WORKDIR))

    if  iscmsconnect:  os.environ['XZ_OPT'] = "--lzma2=preset=2,dict=256MiB"
    else:              os.environ['XZ_OPT'] = "--lzma2=preset=9,dict=512MiB"

    if os.path.isdir("InputCards"): 
      os.system("rm -rf InputCards")

    mkdir("InputCards")

    os.system("cp {CARDSDIR}/{CARDNAME}*.* InputCards".format(CARDSDIR=CARDSDIR,CARDNAME=CARDNAME ))

    EXTRA_TAR_ARGS=""
    if os.path.isfile("{CARDSDIR}/{CARDNAME}_externaltarball.dat".format(CARDSDIR=CARDSDIR,CARDNAME=CARDNAME )):
        EXTRA_TAR_ARGS="external_tarball header_for_madspin.txt "

    ### include merge.pl script for LO event merging 
    if os.path.isfile("merge.pl"):
        EXTRA_TAR_ARGS+="merge.pl "
    os.system("XZ_OPT=\"$XZ_OPT\" tar -cJpsf {PRODHOME}/{CARDNAME}_{scram_arch}_{cmssw_version}_tarball.tar.xz mgbasedir process runcmsgrid.sh InputCards {EXTRA_TAR_ARGS}".format( PRODHOME=PRODHOME, CARDNAME=CARDNAME, scram_arch=scram_arch, cmssw_version=cmssw_version, EXTRA_TAR_ARGS=EXTRA_TAR_ARGS ))
    print("Gridpack created successfully at {PRODHOME}/{CARDNAME}_{scram_arch}_{cmssw_version}_tarball.tar.xz".format(PRODHOME=PRODHOME, CARDNAME=CARDNAME, scram_arch=scram_arch, cmssw_version=cmssw_version))
    print("End of job")

    return


def mkdir(path):
    try:
        os.system("mkdir {}".format(path))
    except:
        print("Directory {} already present, skipping".format(path))
        pass
    
    return 


def write_sh(exec_name, card_name, card_dir, output_folder):
    l = """#! /bin/bash
# Condor scratch dir
condor_scratch=$(pwd)


# Add unzip to the environment
if [ -x $condor_scratch/unzip ]; then
    mkdir $condor_scratch/local_bin
    mv $condor_scratch/unzip $condor_scratch/local_bin
    export PATH="$PATH:$condor_scratch/local_bin"
fi
# Untar input files
ls
tar xfz "{input_files}"

mv condor_sub/{exec_name}.dat ${{condor_scratch}}/{card_name}/{card_name}_gridpack/work/process/madevent/Cards/reweight_card.dat

echo "mg5_path = ${{condor_scratch}}/{card_name}/{card_name}_gridpack/work/MG5_aMC_v2_6_5" >> ${{condor_scratch}}/{card_name}/{card_name}_gridpack/work/process/madevent/Cards/me5_configuration.txt
#echo "cluster_temp_path = None" >> ./madevent/Cards/me5_configuration.txt
#echo "run_mode = 0" >> ./madevent/Cards/me5_configuration.txt 

# Setup CMS framework
export VO_CMS_SW_DIR=/cvmfs/cms.cern.ch
source $VO_CMS_SW_DIR/cmsset_default.sh

# For modified gridpack generation script set this variable to exit after reweight and not create the tarball
export REWEIGHT_ON_CONDOR=true


# Purdue wokaround
unset CXX CC FC
# Run
iscmsconnect=1 bash -x gridpack_generation_EFT.sh {card_name} {card_dir} local REWEIGHT
exitcode=$?
if [ $exitcode -ne 0 ]; then
    echo "Something went wrong while running REWEIGHT step. Exiting now."
    exit $exitcode
fi
# Pack output and condor scratch dir info
cd "${{condor_scratch}}/{card_name}/{card_name}_gridpack/work/process/madevent"
ls
XZ_OPT="--lzma2=preset=9,dict=512MiB" tar -cJpsf "${{condor_scratch}}/{sandbox_output}" "rwgt"

# Stage-out sandbox
# First, try XRootD via stash.osgconnect.net
echo ">> Copying sandbox via XRootD"
xrdcp -f "${{condor_scratch}}/{sandbox_output}" "root://stash.osgconnect.net:1094/${{stash_tmpdir##/stash}}/{sandbox_output}"
exitcode=\$?
if [ $exitcode -eq 0 ]; then
    exit 0
else
    echo "The xrdcp command below failed:"
    echo "xrdcp -f ${{condor_scratch}}$sandbox_output root://stash.osgconnect.net:1094/${{stash_tmpdir##/stash}}/$sandbox_output"
fi
""".format(sandbox_output="{}_output.tar.xz".format(exec_name) , input_files="input_reweight_{}.tar.gz".format(card_name), card_name=card_name, card_dir=card_dir, exec_name=exec_name)

    f = open(output_folder + exec_name + ".sh", "w")
    f.write(l)
    f.close()

    os.system("chmod +x {}".format(output_folder + exec_name + ".sh"))
    return  

def write_jdl(exec_name, card_name, card_dir, output_folder):
    l = """Universe = vanilla 
Executable = {exec_name}.sh
Arguments = {card_name} {card_dir}

Error = condor_log/job.err.$(Cluster)-$(Process) 
Output = condor_log/job.out.$(Cluster)-$(Process) 
Log = condor_log/job.log.$(Cluster) 

transfer_input_files = input_reweight_{card_name}.tar.gz, gridpack_generation_EFT.sh, /usr/bin/unzip
transfer_output_files = {card_name}.log, {exec_name}_output.tar.xz
transfer_output_remaps = \"{card_name}.log = {exec_name}.log\"
+WantIOProxy=true
+IsGridpack=true
+GridpackCard = \"{card_name}\"

+REQUIRED_OS = \"rhel7\"
request_cpus = 2
request_memory = 5Gb
Queue 1
""".format(exec_name=exec_name, card_name=card_name, card_dir=card_dir )

    f = open(output_folder + exec_name + ".jdl", "w")
    f.write(l)
    f.close()
    return 

def write_rew_dict(rew_dict, output_folder, cardname, cardpath):

    for key in rew_dict.keys():
        if not output_folder[-1] == "/": output_folder += "/"


        # writing reweight card
        f = open(output_folder + "rwgt_{}_{}.dat".format(key, cardname), "w")
        for line in rew_dict[key]:
            f.write(line)
        f.close() 

        #writing .jdl
        write_jdl("rwgt_{}_{}".format(key, cardname), cardname, cardpath, output_folder="")

        #writing .sh
        write_sh("rwgt_{}_{}".format(key, cardname), cardname, cardpath, output_folder="")

    return 

def build_rew_dict_scratch(operators, change_process , model):

    rew_d = {}

    mandatory = ["change helicity False\n"]
    mandatory.append("change rwgt_dir rwgt\n")

    if change_process != "": 
        if not change_process.endswith('\n'): change_process += "\n"
        mandatory.append(change_process)

    mandatory.append("\n")
    
    sortedsel = sorted (operators, key = itemgetter (1))

    # We take all 2D combinations of operators, we then reweight to the following
    # components (1,0), (-1,0), (0,1), (0,-1), (1,1) as the matrix element
    # is the same. This is more efficient than generating 5 different reweight dirs.
    # Howvere we need to keep track of the single operators (the (1,0) (0,1)) already studied
    # For the other we just evaluate (1,1)

    done_singles = []

    idx = 0
    for i in range (len (sortedsel)):
        for j in range (i+1, len (sortedsel)):
            tag = sortedsel[i][1] + '_' + sortedsel[j][1] 
            
            rwgt_points = []
            rwgt_points += mandatory

            # first append a comment line
            rwgt_points.append("# {}=1 {}=1 rwgt_{}\n".format(sortedsel[i][1] , sortedsel[j][1], sortedsel[i][1] + "_" + sortedsel[j][1]))
            # change rwgt direcrory 
            rwgt_points.append("change rwgt_dir rwgt/rwgt_{}\n".format(tag))
            # change model
            rwgt_points.append("change model {}-{}_massless\n".format(model, tag))
            # evaluate the mixed term (1,1)
            rwgt_points.append("\n")
            rwgt_points.append("launch --rwgt_name={}\n".format(sortedsel[i][1] + "_" + sortedsel[j][1]))

            rwgt_points.append("\n")
            rwgt_points.append("\n")

            # check if first operator already gen
            if not sortedsel[i][0] in done_singles:
                # If not then evaluate (1,0) and (-1,0)
                for val in [-1 ,1]:
                    tag = sortedsel[i][1]
                    if val == -1: tag += "m1"
                    rwgt_points.append("launch --rwgt_name={}\n".format(tag))
                    rwgt_points.append("    set SMEFT {} {}\n".format(sortedsel[i][0], val))
                    rwgt_points.append("    set SMEFT {} 0\n".format(sortedsel[j][0]))
                    rwgt_points.append("\n")

                done_singles.append(sortedsel[i][0])

            # check if first operator already gen
            if not sortedsel[j][0] in done_singles:
                # If not then evaluate (1,0) and (-1,0)
                for val in [-1 ,1]:
                    tag = sortedsel[j][1]
                    if val == -1: tag += "m1"
                    rwgt_points.append("launch --rwgt_name={}\n".format(tag))
                    rwgt_points.append("    set SMEFT {} {}\n".format(sortedsel[j][0], val))
                    rwgt_points.append("    set SMEFT {} 0\n".format(sortedsel[i][0]))
                    rwgt_points.append("\n")

                done_singles.append(sortedsel[j][0])

            rew_d[idx] = copy.copy(rwgt_points)

            idx += 1

    return rew_d


def build_rew_dict(rew_card):
    f = open(rew_card, 'r')
    contents = f.readlines()

    rew_d = {}

    try:
        contents.index("change rwgt_dir rwgt\n")
    except: 
        sys.exit("[ERROR] \"change rwgt_dir rwgt\" must be present in reweight card")

    #find first launch index 
    for idx,l in enumerate(contents):
        if "launch" in l: break 

    reweight_template = contents[:idx+1]

    rew_d[0] = reweight_template

    contents = contents[idx+1:]
    idx = 1

    reweight_template_copy = copy.copy(reweight_template)
    for line in contents:
        if "launch" not in line:
            if "change model" in line:
                for id_, line_ in enumerate(reweight_template_copy):
                    if "change model" in line_:
                        reweight_template_copy[id_] = line 

            if "change process" in line:
                for id_, line_ in enumerate(reweight_template_copy):
                    if "change process" in line_:
                        reweight_template_copy[id_] = line 

            if "change rwgt_dir" in line:
                for id_, line_ in enumerate(reweight_template_copy):
                    if "change rwgt_dir" in line_ and line_ != "change rwgt_dir rwgt\n":
                        nf = "change rwgt_dir rwgt/" + line.split("/")[-1]
                        reweight_template_copy[id_] = nf 

        else: 
            reweight_template_copy[-1] = line 
            rew_d[idx] =  copy.copy(reweight_template_copy)
            idx += 1
            reweight_template_copy = copy.copy(reweight_template)

    return rew_d



if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Command line parser')
    parser.add_argument('-cn', '--cardname',                    dest='cardname',            help='The name of the cards, <name>_proc_card.dat', required = True)
    parser.add_argument('-cp', '--cardpath',                    dest='cardpath',            help='The path to the cards directory', required = True)
    parser.add_argument('-t', '--task',                        dest='task',               help='Tasks to be executed (separated by a space). Default is all', required = False, nargs = "+", default="all")
    parser.add_argument('-sf', '--subfolder',                   dest='subfolder',           help='The path to the folder where .jid, exec and reweight cards will be saved', required = False, default="condor_sub")
    parser.add_argument('-is5f', '--is5FlavorScheme',           dest='is5FlavorScheme',     help='Is the gridpack intended for 5fs? Default is true', required = False, default=True, action="store_false")
    parser.add_argument('-iscmsc', '--iscmsconnect',            dest='iscmsconnect',        help='Are you working on cmsconnect? Default is true', required = False, default=True, action="store_false")
    parser.add_argument('-cr', '--createreweight',              dest='createreweight',      help='File operator.py will be imported and restriction cards created', required = False, default=False, action="store_true")
    parser.add_argument('-change_process', '--change_process',  dest='change_process',      help='If args.cr is specified, add this to change process in reweight card', required = False, default="", type=str)
    parser.add_argument('-m', '--model',                        dest='model',               help='If args.cr is specified, add this to change the baseline model. Default is SMEFTsim_topU3l_MwScheme_UFO_b_massless', required = False, default="SMEFTsim_topU3l_MwScheme_UFO_b_massless", type=str)


    args = parser.parse_args()

    # Sanity checks

    if not os.path.isdir(args.cardpath): sys.exit("[ERROR] Path {} does not exist".format(args.cardpath))
    if not os.path.isdir(args.cardname): sys.exit("[ERROR] Path {} does not exist".format(args.cardname))
    if not os.path.isfile(args.cardpath + "/" + args.cardname + "_proc_card.dat"): sys.exit("[ERROR] proc card does not exist in {}".format(args.cardpath))
    if not os.path.isfile(args.cardpath + "/" + args.cardname + "_run_card.dat"): sys.exit("[ERROR]  run card does not exist in {}".format(args.cardpath))
    if not args.change_process:
        if not os.path.isfile(args.cardpath + "/" + args.cardname + "_reweight_card.dat"): sys.exit("[ERROR]  reweight card does not exist in {}".format(args.cardpath))
    

    PRODHOME = os.getcwd()
    CARDSDIR=os.path.join(PRODHOME, args.cardpath)
    helpers_dir=os.path.join(PRODHOME, "Utilities")
    WORKDIR = os.path.join(PRODHOME, args.cardname, args.cardname+"_gridpack", "work") 
    genp_name = PRODHOME.split("/bin/MadGraph5_aMCatNLO")[0].split("/")[-1]
    script_dir=os.path.join(PRODHOME.split(genp_name)[0], "genproductions/", "Utilities/scripts")
    cmssw_version="CMSSW_10_6_19"
    scram_arch="slc7_amd64_gcc700"
    MGBASEDIRORIG = "MG5_aMC_v2_6_5"
    patches_directory="./patches"
    utilities_dir="./Utilities"
    plugin_directory="./PLUGIN"

    input_files="input_reweight_{}.tar.gz".format(args.cardname)

    
    #create subfolder to store exec, jid and rew card
    mkdir(args.subfolder)
    # Parsing reweight card
    if not args.createreweight:
        rd = build_rew_dict(args.cardpath + "/" + args.cardname + "_reweight_card.dat")
    else:
        operators = []
        execfile("operators.py")
        rd = build_rew_dict_scratch(operators, args.change_process, args.model)
    
    if any(i in ["rew", "all"] for i in args.task ):
        # write the separate reweight point in a file
        write_rew_dict(rd, args.subfolder, args.cardname, args.cardpath)


    if any(i in ["tar", "all"] for i in args.task ):
        if os.path.isfile(input_files) or os.path.isdir(input_files): 
            print("Tarball allready present. reusing")
        else:
            print("tar -zchvf \"{input_files}\" {rwgt_cards} \"{card_name}\" \"{card_dir}\" \"{patches_directory}\" \"{utilities_dir}\" \"{plugin_directory}\"".format(input_files=input_files, rwgt_cards=" ".join(["\"" + args.subfolder+ "/" "rwgt_" + str(key) + ".dat\"" for key in rd.keys()] ), card_name=args.cardname, card_dir=args.cardpath, patches_directory=patches_directory, utilities_dir=utilities_dir, plugin_directory=plugin_directory))
            os.system("tar -zchvf \"{input_files}\" {rwgt_cards} \"{card_name}\" \"{card_dir}\" \"{patches_directory}\" \"{utilities_dir}\" \"{plugin_directory}\"".format(input_files=input_files, rwgt_cards=" ".join(["\"" + args.subfolder+ "/" "rwgt_" + str(key) + ".dat\"" for key in rd.keys()] ), card_name=args.cardname, card_dir=args.cardpath, patches_directory=patches_directory, utilities_dir=utilities_dir, plugin_directory=plugin_directory))


    if any(i in ["sub", "all"] for i in args.task ):

        print(">> Submitting REWEIGHT condor job and wait")

        mkdir("condor_log")

        for key in rd.keys():
            os.system("condor_submit \"{}\" | tail -n1 | rev | cut -d' ' -f1 | rev".format("rwgt_" + str(key) + ".jdl"))

        #colllecting jobs ids
        out = subprocess.Popen(["condor_q", "-format",  "%d.", "ClusterId", "-format",  "%d\n",  "ProcId"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        stdout,stderr = out.communicate()
        all_procs = stdout.split("\n")[:-1]
        this_procs = all_procs[:len(rd.keys())] # the proc we submitted hopefully are the last ones
        print(all_procs)

        while(any(i in all_procs for i in this_procs)):

            #querying again the condor scheduler
            out = subprocess.Popen(["condor_q", "-format",  "%d.", "ClusterId", "-format",  "%d\n",  "ProcId"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            stdout,stderr = out.communicate()
            all_procs = stdout.split("\n")[:-1]
            print(all_procs)
            time.sleep(5)
        
        print("---> ALL Jobs Finished")

    if any(i in ["mv", "all"] for i in args.task ):

        not_ok = []
        #check for all the outputs
        for key in rd.keys():
            if not os.path.isfile("rwgt_" + str(key) + "_" + args.cardname + "_output.tar.xz"): 
                print("[ERROR] No output found for rwgt_" + str(key) + "_" + args.cardname + "_output.tar.xz")
                not_ok.append("rwgt_" + str(key))
        
        if len(not_ok) > 0: sys.exit(0)
        

        #create rwgt dir if not present
        if not os.path.isdir(args.cardname + "/" + args.cardname + "_gridpack/work/process/madevent/rwgt"):
            mkdir(args.cardname + "/" + args.cardname + "_gridpack/work/process/madevent/rwgt")
        
        for key in rd.keys():
            #os.system("rm rwgt_" + str(key) + ".sh")
            #os.system("rm rwgt_" + str(key) + ".jdl")

            os.system("tar axvf rwgt_" + str(key) + "_" + args.cardname + "_output.tar.xz")

            if not os.path.isdir(args.cardname + "/" + args.cardname + "_gridpack/work/process/madevent/rwgt"):
                os.mkdir(args.cardname + "/" + args.cardname + "_gridpack/work/process/madevent/rwgt")
            os.system("mv rwgt/* " + args.cardname + "/" + args.cardname + "_gridpack/work/process/madevent/rwgt")
            os.system("rm -rf rwgt")
            #os.system("rm rwgt_" + str(key) + "_output.tar.xz")

        # compiling reweight dirs
        precompile_rwgt_dir(os.getcwd() + "/" + args.cardname + "/" + args.cardname + "_gridpack/work/process/madevent")

    
    if any(i in ["clean", "all"] for i in args.task ):

        for key in rd.keys():
            os.system("rm rwgt_" + str(key) + ".sh")
            os.system("rm rwgt_" + str(key) + ".jdl")
            os.system("rm rwgt_" + str(key) + "_" + args.cardname + "_output.tar.xz")

    #############################################

    if any(i in ["prepare", "all"] for i in args.task ):

        print("---> Preparing final gridpack")
        os.chdir(args.cardname + "/" + args.cardname + "_gridpack/work/process")
        os.system("echo \"mg5_path = ../../mgbasedir\" >> ./madevent/Cards/me5_configuration.txt")
        os.system("echo \"cluster_temp_path = None\" >> ./madevent/Cards/me5_configuration.txt")
        os.system("echo \"run_mode = 0\" >> ./madevent/Cards/me5_configuration.txt")

        os.chdir(WORKDIR)



        if os.path.isdir("gridpack"):
            os.syste("rm -rf gridpack")

        mkdir("gridpack")
        os.system("cp -r process gridpack/process")
        os.system("cp -a {}/ gridpack/mgbasedir".format(MGBASEDIRORIG))
            

        os.chdir("gridpack")
        os.system("cp {}/runcmsgrid_LO.sh ./runcmsgrid.sh".format(PRODHOME))

        os.system("sed -i s/SCRAM_ARCH_VERSION_REPLACE/{}/g runcmsgrid.sh".format(scram_arch))
        os.system("sed -i s/CMSSW_VERSION_REPLACE/{}/g runcmsgrid.sh".format(cmssw_version))
        
        pdfExtraArgs=""

        if args.is5FlavorScheme:
            pdfExtraArgs+="--is5FlavorScheme"

        out = subprocess.Popen(["python", "{}/getMG5_aMC_PDFInputs.py".format(script_dir),  "-f",  "systematics", "-c",  "2017", "{}".format(pdfExtraArgs)], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        pdfSysArgs,stderr = out.communicate()

        os.system("sed -i s/PDF_SETS_REPLACE/{pdfSysArgs}/g runcmsgrid.sh".format(pdfSysArgs=pdfSysArgs[:-1]))

        #clean unneeded files for generation
        os.system("{helpers_dir}/cleangridmore.sh".format(helpers_dir=helpers_dir))

        # copy merge.pl from Utilities to allow merging LO events
        os.chdir("{}/gridpack".format(WORKDIR))
        os.system("cp {}/Utilities/merge.pl .".format(PRODHOME)) 

    
    if any(i in ["compress", "all"] for i in args.task ):
        #Finishing the gridpack
        make_tarball(WORKDIR, args.iscmsconnect, PRODHOME, CARDSDIR, args.cardname, scram_arch, cmssw_version)

    print("--> Done <---")
