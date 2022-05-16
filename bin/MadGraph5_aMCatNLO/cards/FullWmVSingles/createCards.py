#!/usr/bin/env python

import os
import argparse

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Command line parser')
    parser.add_argument('--v', dest='verbose', help='Verbose prints', default = False, action = 'store_true', required = False)
    parser.add_argument('--qcd', dest='qcd', help='QCD production. Default is EWK', default = False, action = 'store_true', required = False)
    parser.add_argument('--sm', dest='sm', help='SM cards', default = False, action = 'store_true', required = False)
    parser.add_argument('--smonly', dest='smonly', help='Generate only SM cards', default = False, action = 'store_true', required = False)
    args = parser.parse_args()

    #switchOn = ['2','4','5','7','9','21','22','24','25','29','30','31','32','33','34']
    #switchOn = ['2', '4', '7', '21', '24', '25', '31', '32', '33', '34'] # production succeeded
    #switchOn = ['3', '4', '5', '6', '7', '8', '9', '12', '19', '20', '21', '22', '24', '25', '23', '26', '27', '30', '31', '32', '33', '34', '35', '36', '38', '39', '40', '41', '42', '43', '44', '45', '47', '48', '49', '50', '51', '52', '53']
    #switchOn = [str(i) for i in range(1, 61)]
    #switchOn = ['2','4','5','7','9','21','22','24','25','30','31','32','33','34']
    switchOn = ['4','5','7','9','21','22','24','25','30','31','32','33','34']
    params = [( '1' , 'cG'),
              ('2' , 'cW'),
              ('3' , 'cH'),
              ('4' , 'cHbox'),
              ('5' , 'cHDD'),
              ('6' , 'cHG'),
              ('7' , 'cHW'),
              ('8' , 'cHB'),
              ('9' , 'cHWB'),
              ('10' , 'ceHRe'),
              ('11' , 'cuHRe'),
              ('12' , 'cdHRe'),
              ('13' , 'ceWRe'),
              ('14' , 'ceBRe'),
              ('15' , 'cuGRe'),
              ('16' , 'cuWRe'),
              ('17' , 'cuBRe'),
              ('18' , 'cdGRe'),
              ('19' , 'cdWRe'),
              ('20' , 'cdBRe'),
              ('21' , 'cHl1'),
              ('22' , 'cHl3'),
              ('23' , 'cHe'),
              ('24' , 'cHq1'),
              ('25' , 'cHq3'),
              ('26' , 'cHu'),
              ('27' , 'cHd'),
              ('28' , 'cHudRe'),
              ('29' , 'cll'),
              ('30' , 'cll1'),
              ('31' , 'cqq1'),
              ('32' , 'cqq11'),
              ('33' , 'cqq3'),
              ('34' , 'cqq31'),
              ('35' , 'clq1'),
              ('36' , 'clq3'),
              ('37' , 'cee'),
              ('38' , 'cuu'),
              ('39' , 'cuu1'),
              ('40' , 'cdd'),
              ('41' , 'cdd1'),
              ('42' , 'ceu'),
              ('43' , 'ced'),
              ('44' , 'cud1'),
              ('45' , 'cud8'),
              ('46' , 'cle'),
              ('47' , 'clu'),
              ('48' , 'cld'),
              ('49' , 'cqe'),
              ('50' , 'cqu1'),
              ('51' , 'cqu8'),
              ('52' , 'cqd1'),
              ('53' , 'cqd8'),
              ('54' , 'cledqRe'),
              ('55' , 'cquqd1Re'),
              ('56' , 'cquqd11Re'),
              ('57' , 'cquqd8Re'),
              ('58' , 'cquqd81Re'),
              ('59' , 'clequ1Re'),
              ('60' , 'clequ3Re')]

    if args.qcd:
        MG_constr = 'QCD=99'
    else:
        MG_constr = 'QCD=0'

    proc = ["WmVjj_ewk_dim6"]
   
    counter = 0

    if args.sm:
            counter +=1 
            # clean directory
            prefix = '{0}_SM'.format(proc[0])
            dirname = './{0}_SM/'.format(proc[0])
            if os.path.isdir(dirname):
                os.system('rm -rf ' + dirname)
            os.mkdir(dirname)
            # cards names
            runcard = dirname + prefix + '_run_card.dat'
            proccard = dirname + prefix + '_proc_card.dat'
            # run card
            if args.verbose:
                print ('\n[INFO] producing ' + prefix + '_run_card.dat')
            os.system('cp ./run_card.dat ' + runcard)
            # extramodels card
            if args.verbose:
                print ('[INFO] producing ' + prefix + '_extramodels.dat')
            # proc card
            if args.verbose:
                print ('[INFO] producing ' + prefix + '_proc_card.dat')
            with open(proccard, 'w') as p:
                p.write('set default_unset_couplings 99\n')
                p.write('set group_subprocesses Auto\n')
                p.write('set ignore_six_quark_processes False\n')
                p.write('set loop_optimized_output True\n')
                p.write('set low_mem_multicore_nlo_generation False\n')
                p.write('set loop_color_flows False\n')
                p.write('set gauge unitary\n')
                p.write('set complex_mass_scheme False\n')
                p.write('set max_npoint_for_channel 0\n')
                p.write('define p = g u c d s b u~ c~ d~ s~ b~\n')
                p.write('define j = p\n')
                p.write('define l+ = e+ mu+ ta+\n')
                p.write('define l- = e- mu- ta-\n')
                p.write('define vl = ve vm vt\n')
                p.write('define vl~ = ve~ vm~ vt~\n')
                p.write('import model SMEFTsim_U35_MwScheme_UFO_b_massless-SMlimit_massless\n')
                p.write('generate p p > l- vl~ j j j j SMHLOOP=0 QCD=0\n')
                p.write('output ' + prefix + ' -nojpeg')

    if not args.smonly:
        for param in params:
            if param[0] not in switchOn: continue
            # loop over processes
            for s in ["QU", "LI"]:
                counter +=1
                if s == "LI": step = "NP=1 NP^2==1"
                elif s == "QU": step = "NP=1 NP^2==2"
                # clean directory
                prefix = '{0}_{1}_{2}'.format(proc[0], param[1], s)
                dirname = './{0}_{1}_{2}/'.format(proc[0], param[1], s)
                if os.path.isdir(dirname):
                    os.system('rm -rf ' + dirname)
                os.mkdir(dirname)
                # cards names
                runcard = dirname + prefix + '_run_card.dat'
                proccard = dirname + prefix + '_proc_card.dat'
                # run card
                if args.verbose:
                    print ('\n[INFO] producing ' + prefix + '_run_card.dat')
                os.system('cp ./run_card.dat ' + runcard)
                if args.verbose:
                    print ('[INFO] producing ' + prefix + '_proc_card.dat')
                with open(proccard, 'w') as p:
                    p.write('set default_unset_couplings 99\n')
                    p.write('set group_subprocesses Auto\n')
                    p.write('set ignore_six_quark_processes False\n')
                    p.write('set loop_optimized_output True\n')
                    p.write('set low_mem_multicore_nlo_generation False\n')
                    p.write('set loop_color_flows False\n')
                    p.write('set gauge unitary\n')
                    p.write('set complex_mass_scheme False\n')
                    p.write('set max_npoint_for_channel 0\n')
                    p.write('define p = g u c d s b u~ c~ d~ s~ b~\n')
                    p.write('define j = p\n')
                    p.write('define l+ = e+ mu+ ta+\n')
                    p.write('define l- = e- mu- ta-\n')
                    p.write('define vl = ve vm vt\n')
                    p.write('define vl~ = ve~ vm~ vt~\n')
                    p.write('import model SMEFTsim_U35_MwScheme_UFO_b_massless-{}_massless\n'.format(param[1]))
                    p.write('generate p p > l- vl~ j j j j SMHLOOP=0 QCD=0 {}\n'.format(step))
                    p.write('output ' + prefix + ' -nojpeg')

        from operator import itemgetter
        selected = [x for x in params if x[0] in switchOn]
        sortedsel = sorted (selected, key = itemgetter (1))
        s = "IN"
        for i in range (len (sortedsel)):
           for j in range (i+1, len (sortedsel)):
              counter +=1
              tag = sortedsel[i][1] + '_' + sortedsel[j][1]
              step = 'NP==1  NP' + sortedsel[i][1] + '^2==1   NP' + sortedsel[j][1] + '^2==1'
              # clean directory
              prefix = '{0}_{1}_{2}'.format(proc[0], tag, s)
              dirname = './{0}_{1}_{2}/'.format(proc[0], tag, s)
              if os.path.isdir(dirname):
                  os.system('rm -rf ' + dirname)
              os.mkdir(dirname)
              # cards names
              runcard = dirname + prefix + '_run_card.dat'
              proccard = dirname + prefix + '_proc_card.dat'
              # run card
              if args.verbose:
                  print ('\n[INFO] producing ' + prefix + '_run_card.dat')
              os.system('cp ./run_card.dat ' + runcard)
              if args.verbose:
                  print ('[INFO] producing ' + prefix + '_proc_card.dat')
              with open(proccard, 'w') as p:
                  p.write('set default_unset_couplings 99\n')
                  p.write('set group_subprocesses Auto\n')
                  p.write('set ignore_six_quark_processes False\n')
                  p.write('set loop_optimized_output True\n')
                  p.write('set low_mem_multicore_nlo_generation False\n')
                  p.write('set loop_color_flows False\n')
                  p.write('set gauge unitary\n')
                  p.write('set complex_mass_scheme False\n')
                  p.write('set max_npoint_for_channel 0\n')
                  p.write('define p = g u c d s b u~ c~ d~ s~ b~\n')
                  p.write('define j = p\n')
                  p.write('define l+ = e+ mu+ ta+\n')
                  p.write('define l- = e- mu- ta-\n')
                  p.write('define vl = ve vm vt\n')
                  p.write('define vl~ = ve~ vm~ vt~\n')
                  p.write('import model SMEFTsim_U35_MwScheme_UFO_b_massless-{}_massless\n'.format(tag))
                  p.write('generate p p > l- vl~ j j j j SMHLOOP=0 QCD=0 {}\n'.format(step))
                  p.write('output ' + prefix + ' -nojpeg')
    
print ('{} Cards created successfully'.format(counter))
