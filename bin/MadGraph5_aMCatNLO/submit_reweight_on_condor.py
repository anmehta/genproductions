import os 
import sys
import argparse
import copy

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

mv {exec_name}.dat ${{condor_scratch}}/{card_name}/{card_name}_gridpack/work/process/madevent/Cards/reweight_card.dat

# Setup CMS framework
export VO_CMS_SW_DIR=/cvmfs/cms.cern.ch
source $VO_CMS_SW_DIR/cmsset_default.sh
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
#transfer_output_files = {card_name}.log, {exec_name}_output.tar.xz
#transfer_output_remaps = \"{card_name}.log = {exec_name}.log\"
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
        f = open(output_folder + "rwgt_{}.dat".format(key), "w")
        for line in rew_dict[key]:
            f.write(line)
        f.close() 

        #writing .jdl
        write_jdl("rwgt_{}".format(key), cardname, cardpath, output_folder="")

        #writing .sh
        write_sh("rwgt_{}".format(key), cardname, cardpath, output_folder="")
        #f = open(output_folder + "rwgt_{}.sh".format(key), "w")
        #for line in rew_dict[key]:
        #    f.write(line)
        #f.close() 

    return 

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
    parser.add_argument('-cn', '--cardname',     dest='cardname',     help='The name of the cards, <name>_proc_card.dat', required = True)
    parser.add_argument('-cp', '--cardpath',     dest='cardpath',     help='The path to the cards directory', required = True)
    parser.add_argument('-sf', '--subfolder',     dest='subfolder',     help='The path to the folder where .jid, exec and reweight cards will be saved', required = False, default="condor_sub")


    args = parser.parse_args()

    # Sanity checks

    if not os.path.isdir(args.cardpath): sys.exit("[ERROR] Path {} does not exist".format(args.cardpath))
    if not os.path.isdir(args.cardname): sys.exit("[ERROR] Path {} does not exist".format(args.cardname))
    if not os.path.isfile(args.cardpath + "/" + args.cardname + "_proc_card.dat"): sys.exit("[ERROR] proc card does not exist in {}".format(args.cardpath))
    if not os.path.isfile(args.cardpath + "/" + args.cardname + "_run_card.dat"): sys.exit("[ERROR]  run card does not exist in {}".format(args.cardpath))
    if not os.path.isfile(args.cardpath + "/" + args.cardname + "_reweight_card.dat"): sys.exit("[ERROR]  reweight card does not exist in {}".format(args.cardpath))
    

    patches_directory="./patches"
    utilities_dir="./Utilities"
    plugin_directory="./PLUGIN"

    input_files="input_reweight_{}.tar.gz".format(args.cardname)

    #create subfolder to store exec, jid and rew card
    mkdir(args.subfolder)
    # Parsing reweight card
    rd = build_rew_dict(args.cardpath + "/" + args.cardname + "_reweight_card.dat")
    # write the separate reweight point in a file
    write_rew_dict(rd, args.subfolder, args.cardname, args.cardpath)


    if os.path.isfile(input_files) or os.path.isdir(input_files): 
        print("Tarball allready present. reusing")
    else:
        print("tar -zchvf \"{input_files}\" {rwgt_cards} \"{card_name}\" \"{card_dir}\" \"{patches_directory}\" \"{utilities_dir}\" \"{plugin_directory}\"".format(input_files=input_files, rwgt_cards=" ".join(["\"" + args.subfolder+ "/" "rwgt_" + str(key) + ".dat\"" for key in rd.keys()] ), card_name=args.cardname, card_dir=args.cardpath, patches_directory=patches_directory, utilities_dir=utilities_dir, plugin_directory=plugin_directory))
        os.system("tar -zchvf \"{input_files}\" {rwgt_cards} \"{card_name}\" \"{card_dir}\" \"{patches_directory}\" \"{utilities_dir}\" \"{plugin_directory}\"".format(input_files=input_files, rwgt_cards=" ".join(["\"" + args.subfolder+ "/" "rwgt_" + str(key) + ".dat\"" for key in rd.keys()] ), card_name=args.cardname, card_dir=args.cardpath, patches_directory=patches_directory, utilities_dir=utilities_dir, plugin_directory=plugin_directory))

    #os.system("mv {} {}".format(input_files, args.subfolder))
    #os.system("cp {} {}".format("gridpack_generation_EFT.sh", args.subfolder))
    #os.chdir(args.subfolder)
    mkdir("condor_log")

    print(">> Submitting REWEIGHT condor job and wait")

    for key in rd.keys():
        os.system("condor_submit \"{}\" | tail -n1 | rev | cut -d' ' -f1 | rev".format("rwgt_" + str(key) + ".jdl"))




    print("--> Done <---")